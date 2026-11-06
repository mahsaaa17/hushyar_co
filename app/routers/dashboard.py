"""Dashboard and project overview."""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.core.database import list_projects

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", include_in_schema=False)
def dashboard(request: Request):
	projects = list_projects()
	return templates.TemplateResponse(
		request=request,
		name="dashboard.html",
		context={"projects": projects, "project_count": len(projects)},
	)
