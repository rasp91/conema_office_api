from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import ForeignKey, String

from src.database.base import Base


class SharePointArticleDivision(Base):
    __tablename__ = "kiosk_sharepoint_article_divisions"

    # division is a free-text mirror of whatever SharePoint's "Division" choice field
    # returns - not a fixed enum, so new values added on the SharePoint side flow through
    # without a code/migration change here.
    article_id: Mapped[str] = mapped_column(ForeignKey("kiosk_sharepoint_articles.id", ondelete="CASCADE"), primary_key=True)
    division: Mapped[str] = mapped_column(String(50), primary_key=True)

    article = relationship("SharePointArticle", back_populates="division_links")
