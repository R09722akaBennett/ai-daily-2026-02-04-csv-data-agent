from app.core.csv_agent import profile_csv


def test_profile_counts() -> None:
    prof = profile_csv('a,b
1,2
1,
')
    assert {p.name for p in prof} == {'a','b'}
