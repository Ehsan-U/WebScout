

async def handle_error(request, exception):
    """
    called when an exception is raised.
    """
    return {"message": "Resource not found"}


