"""Quick smoke-test for the Flask API."""
from app import app

client = app.test_client()

# 1. domains
r = client.get('/api/domains')
assert r.status_code == 200
assert len(r.get_json()['domains']) == 12
print('1. /api/domains          OK')

# 2. session start
r = client.post('/api/session/start', json={
    'name': 'SmokeTest',
    'domain': 'UI/UX Design',
    'skill_level': 'beginner',
    'goal': 'Become a designer',
    'weekly_hours': 6,
    'preferred_style': 'mixed',
})
assert r.status_code == 200, r.get_data(as_text=True)
d = r.get_json()
sid = d['profile']['student_id']
print('2. /api/session/start    OK  roadmap_phases =', d['profile']['roadmap_phases'])

# 3. roadmap
r = client.get('/api/roadmap?student_id=' + sid)
assert r.status_code == 200
phases = r.get_json()['roadmap']
assert len(phases) > 0
print('3. /api/roadmap          OK  phases =', len(phases))

# 4. progress
r = client.get('/api/progress?student_id=' + sid)
assert r.status_code == 200
rpt = r.get_json()['report']
print('4. /api/progress         OK  pct =', rpt['completion_percentage'])

# 5. start a course
first_course = phases[0]['courses'][0]
r = client.post('/api/course/start', json={'student_id': sid, 'course': first_course})
assert r.status_code == 200
print('5. /api/course/start     OK  course =', first_course['title'])

# 6. complete the course
r = client.post('/api/course/complete', json={
    'student_id': sid, 'course_id': first_course['id'], 'rating': 5
})
assert r.status_code == 200
print('6. /api/course/complete  OK')

# 7. regenerate roadmap
r = client.post('/api/roadmap/regenerate', json={'student_id': sid})
assert r.status_code == 200
print('7. /api/roadmap/regen    OK  phases =', len(r.get_json()['roadmap']))

# 8. index page
r = client.get('/')
assert r.status_code == 200
assert b'LearnMate' in r.data
print('8. /                     OK  html len =', len(r.data))

# 9. profiles list
r = client.get('/api/profiles')
assert r.status_code == 200
print('9. /api/profiles         OK  count =', len(r.get_json()['profiles']))

print()
print('ALL CHECKS PASSED')
