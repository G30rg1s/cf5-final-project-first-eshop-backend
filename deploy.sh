#!/bin/bash
rsync -avz --delete requirements.txt src wsgi.py ubuntu@ntuacloud:coding-factory-backend
ssh ubuntu@ntuacloud 'source ~/coding-factory-backend/venv/bin/activate && pip install -r ~/coding-factory-backend/requirements.txt'
ssh ubuntu@ntuacloud 'sudo supervisorctl reload'