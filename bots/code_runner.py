import asyncio
from pathlib import Path

class RunnedCodeResult:
    def __init__(self: 'RunnedCodeResult', result: dict):
        """
        RunnedCodeResult type class for CodeRunner.Run asynchronous function results

        Args:
            result: a dictionary that contains these keys values: "stdout", "stderr"
        
        Example:
            >>> test_type = RunnedCodeResult({"stdout": "test", "stderr": ''})
            >>> print(
                test_type.stdout
                )
            'test'
            >>> print(
                test_type.stderr
                )
            ''
        """
        self.result = result
    
    @property
    def stdout(self: 'RunnedCodeResult') -> str:
        return self.result.get("stdout", '')
    
    @property
    def stderr(self: 'RunnedCodeResult') -> str:
        return self.result.get("stderr", '')

class CodeRunner:
    def __init__(self: 'CodeRunner', code: str):
        """
        CodeRunner class for running python3 codes
        
        Args:
            code: a str that contains python3 code
        
        Example:
            >>> import asyncio
            >>> cr = CodeRunner("print('t')")
            >>> result = asyncio.run(cr.Run())
            >>> print(f"Output: {result.stdout}\nErrors: {result.stderr}")
            'Output: t
            Errors: '
        """
        self.code = code
        self.RunnerFilePath = f"{self.curdir}/runner.py"

        with open(self.RunnerFilePath, 'w') as f:
            f.write(self.code)
    
    async def Run(self: 'CodeRunner') -> RunnedCodeResult:
        process = await asyncio.create_subprocess_shell(
            f"python3 {self.RunnerFilePath}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    
        stdout, stderr = await process.communicate()
        
        return RunnedCodeResult({
            "code": self.code,
            "stdout": stdout.decode(),
            "stderr": stderr.decode()
        })
    
    @property
    def curdir(self: 'CodeRunner') -> str:
        return Path(__file__).parent.resolve()

if __name__ == "__main__":
    cr = CodeRunner("print('HelloWorld!')")
    result = asyncio.run(cr.Run())
    print(f"Errors: {result.stderr}")
    print(f"Output: {result.stdout}")
