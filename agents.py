Starting Container
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:40936 - "POST /generate HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/app/agents.py", line 144, in run_all_agents
    parsed = _try_parse_json(raw)
  File "/app/agents.py", line 37, in _try_parse_json
    return json.loads(cleaned)
           ~~~~~~~~~~^^^^^^^^^
  File "/mise/installs/python/3.13.12/lib/python3.13/json/__init__.py", line 352, in loads
    return _default_decoder.decode(s)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^
  File "/mise/installs/python/3.13.12/lib/python3.13/json/decoder.py", line 345, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/mise/installs/python/3.13.12/lib/python3.13/json/decoder.py", line 361, in raw_decode
    obj, end = self.scan_once(s, idx)
               ~~~~~~~~~~~~~~^^^^^^^^
json.decoder.JSONDecodeError: Expecting ',' delimiter: line 115 column 10 (char 5951)
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "/app/agents.py", line 87, in _repair_json
    return _repair_json_once(client, bad_text)
  File "/app/agents.py", line 82, in _repair_json_once
    return _try_parse_json(resp.choices[0].message.content)
  File "/app/agents.py", line 37, in _try_parse_json
    return json.loads(cleaned)
           ~~~~~~~~~~^^^^^^^^^
  File "/mise/installs/python/3.13.12/lib/python3.13/json/__init__.py", line 352, in loads
    return _default_decoder.decode(s)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^
  File "/mise/installs/python/3.13.12/lib/python3.13/json/decoder.py", line 345, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/mise/installs/python/3.13.12/lib/python3.13/json/decoder.py", line 361, in raw_decode
    obj, end = self.scan_once(s, idx)
               ~~~~~~~~~~~~~~^^^^^^^^
json.decoder.JSONDecodeError: Expecting ',' delimiter: line 115 column 10 (char 5951)
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "/app/.venv/lib/python3.13/site-packages/uvicorn/protocols/http/h11_impl.py", line 410, in run_asgi
    await self.app(scope, receive, _send)
  File "/app/.venv/lib/python3.13/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/app/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.scope, self.receive, self.send
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/app/.venv/lib/python3.13/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.13/site-packages/fastapi/applications.py", line 1160, in __call__
    await super().__call__(scope, receive, send)
  File "/app/.venv/lib/python3.13/site-packages/starlette/applications.py", line 107, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/app/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/app/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 164, in __call__
  File "/app/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 116, in app
    response = await f(request)
    raise exc
  File "/app/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/app/.venv/lib/python3.13/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/app/.venv/lib/python3.13/site-packages/starlette/routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/app/.venv/lib/python3.13/site-packages/starlette/routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "/app/.venv/lib/python3.13/site-packages/starlette/routing.py", line 290, in handle
    await self.app(scope, receive, send)
  File "/app/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 130, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/app/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/app/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
    return await get_async_backend().run_sync_in_worker_thread(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        func, args, abandon_on_cancel=abandon_on_cancel, limiter=limiter
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/app/.venv/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 2502, in run_sync_in_worker_thread
               ^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 670, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/app/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 326, in run_endpoint_function
    return await run_in_threadpool(dependant.call, **values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.13/site-packages/starlette/concurrency.py", line 32, in run_in_threadpool
    return await anyio.to_thread.run_sync(func)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.13/site-packages/anyio/to_thread.py", line 63, in run_sync
    return await future
           ^^^^^^^^^^^^
  File "/app/.venv/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 986, in run
