echo "Waiting redis"
python3 wait_for_redis.py

echo "Waiting elastic"
#python3 wait_for_elastic.py

echo "Run fast api"
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
