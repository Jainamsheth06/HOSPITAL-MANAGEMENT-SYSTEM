cd /home/MediNEXA
unzip -o final_update.zip
python manage.py collectstatic --noinput
touch /var/www/*_wsgi.py
echo 'DEPLOYMENT SUCCESSFUL FOR REAL!'
