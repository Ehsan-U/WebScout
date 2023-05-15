import fastapi
import routes
from fastapi.middleware.cors import CORSMiddleware
import exceptions


app = fastapi.FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(Exception, exceptions.handle_error)
app.include_router(routes.router, prefix='/webscout')
