import enum
from datetime import datetime, date

# --- Helper Parsers ---
def parse_date(val):
    if not val:
        return None
    if isinstance(val, (date, datetime)):
        return val
    try:
        # Strip time if present
        date_str = val.split("T")[0]
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return val

def parse_datetime(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        val_clean = val.replace("Z", "").split("+")[0]
        if "T" in val_clean:
            if "." in val_clean:
                return datetime.strptime(val_clean, "%Y-%m-%dT%H:%M:%S.%f")
            return datetime.strptime(val_clean, "%Y-%m-%dT%H:%M:%S")
        else:
            if "." in val_clean:
                return datetime.strptime(val_clean, "%Y-%m-%d %H:%M:%S.%f")
            return datetime.strptime(val_clean, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return val

# --- Dynamic Operator Overloader ---
class FieldRef:
    def __init__(self, name):
        self.name = name

    def asc(self):
        return ("asc", self.name)

    def desc(self):
        return ("desc", self.name)

    def __eq__(self, other):
        return ("eq", self.name, other)

    def __ne__(self, other):
        return ("ne", self.name, other)

    def __lt__(self, other):
        return ("lt", self.name, other)

    def __le__(self, other):
        return ("le", self.name, other)

    def __gt__(self, other):
        return ("gt", self.name, other)

    def __ge__(self, other):
        return ("ge", self.name, other)

    def in_(self, other_list):
        return ("in", self.name, other_list)

class ModelMeta(type):
    def __getattr__(cls, name):
        return FieldRef(name)

class BaseJsonModel(metaclass=ModelMeta):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
            
    def dict(self):
        return self.__dict__

# --- Models ---

class JournalPhase(enum.Enum):
    scaffolding = "scaffolding"
    writing = "writing"
    evaluation = "evaluation"
    completed = "completed"

class User(BaseJsonModel):
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.username = kwargs.get("username")
        self.email = kwargs.get("email")
        self.realname = kwargs.get("realname")
        self.student_id = kwargs.get("student_id")
        self.group = kwargs.get("group")
        self.hashed_password = kwargs.get("hashed_password")
        self.is_admin = bool(kwargs.get("is_admin", False))
        self.created_at = parse_datetime(kwargs.get("created_at"))
        
        # Backward compatibility fields expected by UserOut schema
        self.font_preference = kwargs.get("font_preference", "Inter")
        self.notifications_enabled = bool(kwargs.get("notifications_enabled", False))
        
        super().__init__(**kwargs)

class Journal(BaseJsonModel):
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.user_id = kwargs.get("user_id")
        self.journal_date = parse_date(kwargs.get("journal_date"))
        self.title = kwargs.get("title")
        self.content = kwargs.get("content", "")
        self.writing_time_spend = float(kwargs.get("writing_time_spend") or 0.0)
        
        # Handle Enum type for writing_phase
        phase_val = kwargs.get("writing_phase")
        if isinstance(phase_val, str):
            try:
                self.writing_phase = JournalPhase[phase_val]
            except KeyError:
                self.writing_phase = JournalPhase.completed
        elif isinstance(phase_val, JournalPhase):
            self.writing_phase = phase_val
        else:
            self.writing_phase = JournalPhase.completed
            
        self.created_at = parse_datetime(kwargs.get("created_at"))
        self.updated_at = parse_datetime(kwargs.get("updated_at"))
        
        super().__init__(**kwargs)