from collections.abc import Sequence

from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import status, HTTPException, APIRouter, Depends

from src.database.models.kiosk_team_members import TeamMember
from src.kiosk.team_members.schemas import (
    TeamMemberUpdateModel,
    TeamMemberCreateModel,
    TeamMemberModel,
    ResponseModel,
)
from src.database import get_db
from src.upload import delete_file
from src.logger import app_logger
from src.auth import get_auth_user

router = APIRouter()


def _get_team_member_or_404(member_id: int, db: Session) -> TeamMember:
    item = db.execute(select(TeamMember).where(TeamMember.id == member_id)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found.")
    return item


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get Team Members",
    response_model=list[TeamMemberModel],
)
def get_team_members(db: Session = Depends(get_db)) -> Sequence[TeamMember]:
    try:
        items = (
            db.execute(
                select(TeamMember)
                .where(TeamMember.is_visible == True)  # noqa: E712
                .order_by(TeamMember.last_name.asc(), TeamMember.first_name.asc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch team members.")


@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    name="Get All Team Members (Admin)",
    dependencies=[Depends(get_auth_user)],
    response_model=list[TeamMemberModel],
)
def get_all_team_members(db: Session = Depends(get_db)) -> Sequence[TeamMember]:
    try:
        items = db.execute(select(TeamMember).order_by(TeamMember.last_name.asc(), TeamMember.first_name.asc())).scalars().all()
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch team members.")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create Team Member",
    dependencies=[Depends(get_auth_user)],
    response_model=TeamMemberModel,
)
def create_team_member(data: TeamMemberCreateModel, db: Session = Depends(get_db)) -> TeamMember:
    try:
        item = TeamMember(
            first_name=data.first_name,
            last_name=data.last_name,
            position=data.position,
            photo_path=data.photo_path,
            bio=data.bio,
            is_visible=data.is_visible,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create team member.")


@router.put(
    "/{member_id}",
    status_code=status.HTTP_200_OK,
    name="Update Team Member",
    dependencies=[Depends(get_auth_user)],
    response_model=TeamMemberModel,
)
def update_team_member(member_id: int, data: TeamMemberUpdateModel, db: Session = Depends(get_db)) -> TeamMember:
    try:
        item = _get_team_member_or_404(member_id, db)

        if data.first_name is not None:
            item.first_name = data.first_name
        if data.last_name is not None:
            item.last_name = data.last_name
        if data.is_visible is not None:
            item.is_visible = data.is_visible
        # Optional text fields can be explicitly cleared by sending null
        if "position" in data.model_fields_set:
            item.position = data.position
        if "bio" in data.model_fields_set:
            item.bio = data.bio
        if "photo_path" in data.model_fields_set:
            # Delete old photo if being replaced or cleared
            if item.photo_path and item.photo_path != data.photo_path:
                delete_file(item.photo_path)
            item.photo_path = data.photo_path

        db.commit()
        db.refresh(item)
        return item
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update team member.")


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Team Member",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_team_member(member_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        item = _get_team_member_or_404(member_id, db)

        if item.photo_path:
            delete_file(item.photo_path)

        db.delete(item)
        db.commit()
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete team member.")
