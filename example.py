from sanic import Sanic, Request
import sanic
import redis.asyncio as redis
from limiter import SanicLimiter, RateLimiter, TooManyRequests


app = Sanic(__name__)


async def init_limiter(app: Sanic, loop):
    @app.on_request
    async def on_request(request: Request):
        if hasattr(request.route.ctx, "limiter"):
            limiter = request.route.ctx.limiter
            if isinstance(limiter, list):
                for l in limiter:
                    await l(request)
            else:
                await limiter(request)

    await SanicLimiter.init(redis.from_url("redis://localhost", encoding="utf8"))


async def close_limiter(app: Sanic, loop):
    await SanicLimiter.close()


app.before_server_start(init_limiter)
app.after_server_stop(close_limiter)


@app.exception(TooManyRequests)
async def too_many_requests(request: Request, exc: TooManyRequests):
    return sanic.json({
        "error": "Too many requests"
    }, exc.status_code)


@app.get("/", ctx_limiter=RateLimiter(times=1, seconds=1))
async def hello_world(request: Request):
    return sanic.json({
        "message": "Hello World!"
    })


@app.get("/dependent/<view>", ctx_limiter=RateLimiter(times=1, seconds=1) & RateLimiter(times=5, hours=1))
async def dependent_view(request: Request, view):
    return sanic.json({
        "message": "Hello World!"
    })


if __name__ == '__main__':

    app.run()