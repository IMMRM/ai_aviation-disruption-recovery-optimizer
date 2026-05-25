import importlib.util
from pathlib import Path


def load_generator_module():
    path = Path(__file__).resolve().parents[1] / "generate_operational_data.py"
    spec = importlib.util.spec_from_file_location("generate_operational_data", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_database_url_percent_encodes_special_characters():
    module = load_generator_module()

    assert module.DATABASE_URL == (
        "postgresql://postgres:Tiger%40Dev2209@"
        "db.pfmvgdmiufocejfynizq.supabase.co:5432/postgres"
    )
