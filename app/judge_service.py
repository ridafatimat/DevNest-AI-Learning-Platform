# app/judge_service.py
import os
import httpx
import asyncio
import base64
from typing import Optional, Dict, Any, List


class JudgeService:
    def __init__(self) -> None:
        self.base_url = os.getenv("JUDGE0_URL", "https://ce.judge0.com")
        self.api_key: Optional[str] = os.getenv("JUDGE0_API_KEY")
        self.timeout = int(os.getenv("JUDGE0_TIMEOUT", "5"))
        self.memory_limit = int(os.getenv("JUDGE0_MEMORY_LIMIT", "128000"))
        self.cpu_time_limit = int(os.getenv("JUDGE0_CPU_TIME_LIMIT", "5"))

        self.language_map: Dict[str, int] = {
            "python": 71,
            "python3": 71,
            "c": 50,
            "cpp": 54,
            "c++": 54,
            "java": 62,
            "javascript": 63,
            "js": 63,
            "go": 60,
            "rust": 73,
        }

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _sanitize_code(self, code: str) -> str:
        code = code.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
        if len(code) > 100_000:
            raise ValueError("Code exceeds maximum size limit (100kB)")
        return code

    def _get_language_id(self, lang: str) -> int:
        lang_lower = lang.lower().strip()
        if lang_lower not in self.language_map:
            raise ValueError(
                f"Unsupported language '{lang}'. "
                f"Supported: {list(self.language_map.keys())}"
            )
        return self.language_map[lang_lower]

    def _encode_base64(self, text: str) -> str:
        """Encode string to base64"""
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    def _decode_base64(self, text: str) -> str:
        """Decode base64 string back to normal text"""
        if not text:
            return ""
        return base64.b64decode(text).decode('utf-8')

    async def _wait_for_result(
        self,
        token: str,
        max_retries: int = 30,
        retry_delay: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Poll Judge0 with base64_encoded=true
        """
        get_url = f"{self.base_url}/submissions/{token}?base64_encoded=true"

        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(max_retries):
                resp = await client.get(get_url, headers=self._get_headers())

                if resp.status_code != 200:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                    raise Exception(
                        f"Judge0 fetch error {resp.status_code}: {resp.text}"
                    )

                result = resp.json()
                status_id = result.get("status", {}).get("id", 0)

                if status_id >= 3:
                    # Decode base64 fields
                    if result.get("stdout"):
                        result["stdout"] = self._decode_base64(result["stdout"])
                    if result.get("stderr"):
                        result["stderr"] = self._decode_base64(result["stderr"])
                    if result.get("compile_output"):
                        result["compile_output"] = self._decode_base64(result["compile_output"])
                    return result

                await asyncio.sleep(retry_delay)

            raise Exception("Judge0 polling exceeded max retries")

    async def run_code(
        self,
        code: str,
        language: str,
        stdin: Optional[str] = None,
        expected_output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run code with base64 encoding enabled
        """
        sanitized_code = self._sanitize_code(code)
        language_id = self._get_language_id(language)

        # Encode all text fields to base64
        payload = {
            "source_code": self._encode_base64(sanitized_code),
            "language_id": language_id,
            "stdin": self._encode_base64(stdin or ""),
            "cpu_time_limit": self.cpu_time_limit,
            "memory_limit": self.memory_limit,
            "wall_time_limit": self.timeout,
        }

        # Add expected_output if provided
        if expected_output is not None:
            payload["expected_output"] = self._encode_base64(expected_output)

        # Use base64_encoded=true
        submit_url = f"{self.base_url}/submissions?base64_encoded=true&wait=false"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    submit_url,
                    json=payload,
                    headers=self._get_headers(),
                )
            except httpx.TimeoutException:
                raise Exception("Judge0 submission timeout")

        if resp.status_code not in (200, 201):
            raise Exception(
                f"Judge0 submission failed: {resp.status_code} - {resp.text}"
            )

        submission = resp.json()
        token = submission.get("token")
        if not token:
            raise Exception("Judge0 did not return a submission token")

        result = await self._wait_for_result(token)

        status_obj = result.get("status", {})
        status_desc = status_obj.get("description", "Unknown")
        status_id = status_obj.get("id", 0)
        stdout_val = (result.get("stdout") or "").rstrip("\n")

        passed = (
            None
            if expected_output is None
            else (status_id == 3 and stdout_val.strip() == expected_output.strip())
        )

        return {
            "status": status_desc,
            "status_id": status_id,
            "stdout": stdout_val,
            "stderr": result.get("stderr", "") or "",
            "compile_output": result.get("compile_output", "") or "",
            "time": result.get("time"),
            "memory": result.get("memory"),
            "exit_code": result.get("exit_code"),
            "exit_signal": result.get("exit_signal"),
            "token": token,
            "passed": passed,
        }

    async def judge_submission(
        self,
        code: str,
        language: str,
        test_cases: List[Dict[str, Any]],
        hidden_test_cases: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Run multiple test cases with base64 encoding
        """
        sanitized_code = self._sanitize_code(code)
        _ = self._get_language_id(language)

        all_test_cases = list(test_cases or [])
        if hidden_test_cases:
            all_test_cases.extend(hidden_test_cases)

        if not all_test_cases:
            raise ValueError("No test cases provided")

        results: List[Dict[str, Any]] = []
        passed_count = 0
        total_tests = len(all_test_cases)

        for idx, tc in enumerate(all_test_cases):
            stdin = tc.get("stdin", "")
            expected_output = tc.get("expected_output", "")
            is_hidden = idx >= len(test_cases)

            try:
                run_result = await self.run_code(
                    code=sanitized_code,
                    language=language,
                    stdin=stdin,
                    expected_output=expected_output,
                )

                test_passed = (
                    run_result.get("status_id") == 3
                    and run_result.get("passed", False)
                )

                if test_passed:
                    passed_count += 1

                tr = {
                    "test_case_id": tc.get("id", f"test_{idx}"),
                    "passed": test_passed,
                    "status": run_result.get("status"),
                    "status_id": run_result.get("status_id"),
                    "stdout": "" if is_hidden else run_result.get("stdout", ""),
                    "stderr": "" if is_hidden else run_result.get("stderr", ""),
                    "expected_output": "" if is_hidden else expected_output,
                    "compile_output": run_result.get("compile_output", ""),
                    "time": run_result.get("time"),
                    "memory": run_result.get("memory"),
                    "exit_code": run_result.get("exit_code"),
                    "is_hidden": is_hidden,
                }
                results.append(tr)

                if run_result.get("status_id") == 6:
                    for j in range(idx + 1, total_tests):
                        tc2 = all_test_cases[j]
                        rem_hidden = j >= len(test_cases)
                        results.append(
                            {
                                "test_case_id": tc2.get("id", f"test_{j}"),
                                "passed": False,
                                "status": "Compilation Error",
                                "status_id": 6,
                                "stdout": "",
                                "stderr": "",
                                "expected_output": "",
                                "compile_output": run_result.get("compile_output", ""),
                                "time": None,
                                "memory": None,
                                "exit_code": None,
                                "is_hidden": rem_hidden,
                            }
                        )
                    break

            except Exception as e:
                results.append(
                    {
                        "test_case_id": tc.get("id", f"test_{idx}"),
                        "passed": False,
                        "status": "Execution Error",
                        "status_id": -1,
                        "stdout": "",
                        "stderr": "" if is_hidden else str(e),
                        "expected_output": "" if is_hidden else expected_output,
                        "compile_output": "",
                        "time": None,
                        "memory": None,
                        "exit_code": None,
                        "is_hidden": is_hidden,
                    }
                )

        score = (passed_count / total_tests * 100) if total_tests else 0.0

        if passed_count == total_tests:
            verdict = "Accepted"
        elif any(r.get("status_id") == 6 for r in results):
            verdict = "Compilation Error"
        elif any(r.get("status_id") == 5 for r in results):
            verdict = "Time Limit Exceeded"
        elif any(r.get("status_id") == 4 for r in results):
            verdict = "Runtime Error"
        else:
            verdict = "Wrong Answer"

        return {
            "verdict": verdict,
            "score": round(score, 2),
            "passed_tests": passed_count,
            "total_tests": total_tests,
            "results": results,
        }


judge_service = JudgeService()