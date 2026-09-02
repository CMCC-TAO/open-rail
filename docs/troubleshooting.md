# Troubleshooting

[中文版本](troubleshooting.zh-CN.md)

- If the web client does not start, check whether the configured port is already in use.
- If the browser cannot connect, verify that `run_web_client.py` is listening on the expected host and port.
- If model loading fails, confirm the checkpoint path and Python environment.
- If robot control is unavailable, switch to mock mode first to isolate the issue.