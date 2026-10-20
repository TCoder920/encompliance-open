import os,sys,secrets,tempfile
from pathlib import Path
from datetime import datetime
repo=Path(__file__).resolve().parents[1] / 'encompliance-backend'
os.chdir(repo);sys.path.insert(0,str(repo))
os.environ.update(DATABASE_URL='sqlite:///'+str(Path(tempfile.mkdtemp())/'auth.db'),OPENAI_API_KEY='test-placeholder',STRIPE_SECRET_KEY='test-placeholder',STRIPE_PUBLISHABLE_KEY='test-placeholder',ENABLE_BACKGROUND_JOBS='false')
for k in ['SECRET_KEY','JWT_SECRET_KEY','SUPPORT_PORTAL_SECRET_KEY']:os.environ[k]=secrets.token_urlsafe(48)
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.auth.utils import get_password_hash
from fastapi.testclient import TestClient
with SessionLocal() as db:
 u=User(username='migration-user',email='migration@example.com',hashed_password=get_password_hash('Synthetic-test-password-123!'),full_name='Synthetic User',is_active=True,email_verified=True,last_login=datetime.utcnow())
 db.add(u);db.commit()
with TestClient(app) as client:
 assert client.get('/health').status_code == 200
 body={'username':'migration-user','password':'Synthetic-test-password-123!'}
 for kwargs in [{'json':body},{'data':body}]:
  response=client.post('/api/v1/login',**kwargs);assert response.status_code==200, response.status_code
  assert response.json().get('access_token')
 with SessionLocal() as db:
  u=db.query(User).filter(User.username=='migration-user').one();u.is_active=False;db.commit()
 assert client.post('/api/v1/login',json=body).status_code==403
 assert client.post('/api/v1/login',data=body).status_code==403
 assert client.post('/api/v1/email-login',json={'email':'migration@example.com','password':body['password']}).status_code==403
print('AUTH_SMOKE_PASSED: JSON/form login and inactive-account rejection across legacy endpoints')
