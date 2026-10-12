from module9_antigents.service import validate_request
import pytest

def test_request_schema():
    assert validate_request({'role':'actor','prompt':'ECA 30'}) == ('actor','ECA 30','')
    assert validate_request({'role':'antigent','prompt':'ECA 30','candidate':'01010101'})[0]=='antigent'
    with pytest.raises(ValueError): validate_request({'role':'antigent','prompt':'ECA 30'})
    with pytest.raises(ValueError): validate_request({'role':'actor','prompt':'x'*5000})
    with pytest.raises(ValueError): validate_request({'role':'rogue','prompt':'hi'})
