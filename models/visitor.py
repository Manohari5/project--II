from datetime import date
from extensions import db


class VisitorLog(db.Model):
    """One row per calendar day, with a running visit count for that day."""
    __tablename__ = "visitor_logs"

    id = db.Column(db.Integer, primary_key=True)
    visit_date = db.Column(db.Date, unique=True, nullable=False, default=date.today)
    count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<VisitorLog {self.visit_date}: {self.count}>"
