import os
from fastapi import FastAPI

app = FastAPI()
FLAG = os.getenv("CTF_FLAG")


def format_flag(value: str) -> str:
    return f"FLAG{{{value}}}"


@app.get("/flag")
def get_flag():
    flag_output = format_flag(FLAG)
    return {"flag": flag_output}
