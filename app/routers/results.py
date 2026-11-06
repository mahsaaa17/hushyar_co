"""Analysis result, category, paradigm, and relationship views."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.core.database import get_project
from app.services.analysis_service import prepare_analysis_results

router = APIRouter(prefix="/results", tags=["results"])
templates = Jinja2Templates(directory="app/templates")


def _project_or_404(project_id: str):
	project = get_project(project_id)
	if project is None:
		raise HTTPException(status_code=404, detail="پروژه پیدا نشد.")
	if not project.get("analysis"):
		raise HTTPException(status_code=409, detail="هنوز تحلیل JSON برای این پروژه ثبت نشده است.")
	return project


@router.get("/{project_id}")
def results_page(request: Request, project_id: str):
	project = _project_or_404(project_id)
	return templates.TemplateResponse(
		request=request,
		name="reports.html",
		context={"project": project, "results": prepare_analysis_results(project["analysis"])},
	)


@router.get("/{project_id}/categories")
def categories_page(request: Request, project_id: str):
	project = _project_or_404(project_id)
	return templates.TemplateResponse(
		request=request,
		name="categories.html",
		context={"project": project, "analysis": project["analysis"]},
	)


@router.get("/{project_id}/paradigm")
def paradigm_page(request: Request, project_id: str):
	project = _project_or_404(project_id)
	return templates.TemplateResponse(
		request=request,
		name="paradigm.html",
		context={
			"project": project,
			"analysis": project["analysis"],
			"results": prepare_analysis_results(project["analysis"]),
		},
	)


@router.get("/{project_id}/relationships")
def relationships_page(request: Request, project_id: str):
	project = _project_or_404(project_id)
	return templates.TemplateResponse(
		request=request,
		name="relationships.html",
		context={"project": project},
	)
