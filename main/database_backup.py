import os
import subprocess
import shutil
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.paginator import Paginator
from .models import DatabaseBackup


# ============================================
# Helper function to check if request is AJAX
# ============================================
def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


# ============================================
# Backup View (Main Page)
# ============================================
@login_required(login_url='/401/')
def backup_view(request):
    backups_list = DatabaseBackup.objects.filter(user=request.user)
    paginator = Paginator(backups_list, 10)
    page_number = request.GET.get('page', 1)
    backups = paginator.get_page(page_number)
    
    context = {
        'backups': backups,
        'paginator': paginator,
    }
    return render(request, 'Backup/backup.html', context)


# ============================================
# Create Backup View
# ============================================
@login_required(login_url='/401/')
def create_backup(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        notes = request.POST.get('notes', '').strip()
        
        # Database credentials
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']
        
        # Create backup directory if not exists
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{db_name}_{timestamp}.sql"
        file_path = os.path.join(backup_dir, filename)
        
        # Set environment variable for password
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Run pg_dump command
        command = [
            'pg_dump',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-d', db_name,
            '-F', 'p',  # Plain text format
            '-f', file_path
        ]
        
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return JsonResponse({
                'success': False, 
                'message': f'Backup failed: {result.stderr}', 
                'type': 'error'
            })
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Save backup record to database
        backup = DatabaseBackup.objects.create(
            user=request.user,
            filename=filename,
            file_path=f'backups/{filename}',
            file_size=file_size,
            notes=notes
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Backup created successfully',
            'type': 'success',
            'backup': {
                'id': backup.id,
                'filename': backup.filename,
                'file_size': backup.get_file_size_display(),
                'created_at': backup.get_created_at_local().strftime('%b %d, %Y %I:%M %p'),
                'notes': backup.notes or ''
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'An error occurred: {str(e)}', 
            'type': 'error'
        })


# ============================================
# Download Backup View
# ============================================
@login_required(login_url='/401/')
def download_backup(request, backup_id):
    try:
        backup = get_object_or_404(DatabaseBackup, id=backup_id, user=request.user)
        file_path = os.path.join(settings.MEDIA_ROOT, str(backup.file_path))
        
        if not os.path.exists(file_path):
            raise Http404("Backup file not found")
        
        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=backup.filename
        )
        return response
        
    except DatabaseBackup.DoesNotExist:
        raise Http404("Backup not found")


# ============================================
# Restore Backup View
# ============================================
@login_required(login_url='/401/')
def restore_backup(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        backup_id = request.POST.get('backup_id')
        uploaded_file = request.FILES.get('backup_file')
        
        # Determine file path
        if backup_id:
            # Restore from existing backup
            backup = get_object_or_404(DatabaseBackup, id=backup_id, user=request.user)
            file_path = os.path.join(settings.MEDIA_ROOT, str(backup.file_path))
            
            if not os.path.exists(file_path):
                return JsonResponse({
                    'success': False, 
                    'message': 'Backup file not found', 
                    'type': 'error'
                })
        elif uploaded_file:
            # Restore from uploaded file
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_restore')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
        else:
            return JsonResponse({
                'success': False, 
                'message': 'No backup selected', 
                'type': 'error'
            })
        
        # Database credentials
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']
        
        # Set environment variable for password
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Drop and recreate database connections (terminate existing connections)
        terminate_command = [
            'psql',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-d', 'postgres',
            '-c', f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{db_name}' AND pid <> pg_backend_pid();"
        ]
        
        subprocess.run(terminate_command, env=env, capture_output=True, text=True)
        
        # Run psql to restore
        restore_command = [
            'psql',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-d', db_name,
            '-f', file_path
        ]
        
        result = subprocess.run(
            restore_command,
            env=env,
            capture_output=True,
            text=True
        )
        
        # Clean up temp file if uploaded
        if uploaded_file and os.path.exists(file_path):
            os.remove(file_path)
        
        if result.returncode != 0 and 'ERROR' in result.stderr:
            return JsonResponse({
                'success': False, 
                'message': f'Restore failed: {result.stderr[:200]}', 
                'type': 'error'
            })
        
        return JsonResponse({
            'success': True,
            'message': 'Database restored successfully. Please refresh the page.',
            'type': 'success'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'An error occurred: {str(e)}', 
            'type': 'error'
        })


# ============================================
# Delete Backup View
# ============================================
@login_required(login_url='/401/')
def delete_backup(request, backup_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        backup = get_object_or_404(DatabaseBackup, id=backup_id, user=request.user)
        filename = backup.filename
        
        # Delete file from media folder
        file_path = os.path.join(settings.MEDIA_ROOT, str(backup.file_path))
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete database record
        backup.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Backup "{filename}" deleted successfully',
            'type': 'success'
        })
        
    except DatabaseBackup.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Backup not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'An error occurred: {str(e)}', 
            'type': 'error'
        })


# ============================================
# Get Backup Details
# ============================================
@login_required(login_url='/401/')
def get_backup(request, backup_id):
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        backup = get_object_or_404(DatabaseBackup, id=backup_id, user=request.user)
        
        return JsonResponse({
            'success': True,
            'backup': {
                'id': backup.id,
                'filename': backup.filename,
                'file_size': backup.get_file_size_display(),
                'created_at': backup.get_created_at_local().strftime('%b %d, %Y %I:%M %p'),
                'notes': backup.notes or ''
            }
        })
        
    except DatabaseBackup.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Backup not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred', 'type': 'error'})


# ============================================
# Get All Backups (for restore modal)
# ============================================
@login_required(login_url='/401/')
def get_all_backups(request):
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        backups = DatabaseBackup.objects.filter(user=request.user)
        backups_list = [{
            'id': b.id,
            'filename': b.filename,
            'file_size': b.get_file_size_display(),
            'created_at': b.get_created_at_local().strftime('%b %d, %Y %I:%M %p'),
        } for b in backups]
        
        return JsonResponse({
            'success': True,
            'backups': backups_list
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred', 'type': 'error'})