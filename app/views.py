from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from app.models import Movie
from register.models import Meal
from register.forms import EditInfoForm
import subprocess
import os
from django.templatetags.static import static
from django.utils import timezone
import time
import paramiko
import json, csv
import shutil
import pathlib

# --- Remote inference configuration ---
# This project originally ran inference on a separate machine (SSH/SFTP + docker exec).
# For GitHub, credentials are intentionally NOT included. Configure via environment variables.
#
# Set INFERENCE_MODE=demo to skip SSH and use local placeholder outputs (useful for portfolio/demo).

INFERENCE_MODE = os.getenv("INFERENCE_MODE", "remote")  # remote | demo

def _env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val

def upload_image(request):
    if request.method == 'POST':
        image = request.FILES['image']
        username = request.user.username
        received_img_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static\\received_img')
        meal_data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static\\meal_data')
        meal_images_folder = os.path.join(meal_data_folder, 'meal_images')
        segmented_images_folder = os.path.join(meal_data_folder, 'segmented_images')
        json_folder = os.path.join(meal_data_folder, 'json_analysis_results')
        
        # Temp file naming : username^temp.png
        # If user saves it : username^date^time.png
        # I didnt use _ to seperate because username might contain that
        temp_image_path = os.path.join(meal_images_folder, f'{username}^temp.png')

        with open(temp_image_path, 'wb') as temp_image:
            for chunk in image.chunks():
                temp_image.write(chunk)
        
        # I dont have GPU locally, so I SCP images for inference at <remote-inference-host>
        # After that I download it
        scp_upload(source_path=temp_image_path)
        temp_segmented_image_path = os.path.join(segmented_images_folder, f'{username}^temp.png')
        temp_json_result_path = os.path.join(json_folder, f'{username}^temp.json')
        scp_download(segmented_image_destination=temp_segmented_image_path, json_result_destination=temp_json_result_path)

        # load the json analysis results(area of each ingredients) to a dictionary
        food_area_json = os.path.join(json_folder, f'{username}^temp.json')  
        with open(food_area_json, 'r') as file:
            json_data = file.read()
        food_area_dictionary = json.loads(json_data)
        # define variables to be used and the path of the CSV reference file for food nutrients data 
        detected_ingredients = [] # 出現的食物列表
        nutrition_components = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # 六大營養指標(公克)
        vitamines = [0.0, 0.0, 0.0, 0.0] # 維生素ADEK的含量
        category_7_food = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # 七大類食物的面積
        nutrition_csv_path = os.path.join(received_img_folder, 'nutrition_new.csv')
        # open the CSV refernece file and find nutrient data for the foods appeared in the food_area_dictionary (food area from json analysis results)
        with open(nutrition_csv_path, 'r', encoding='utf-8') as nutrition_csv:
            csv_reader = csv.reader(nutrition_csv)
            next(csv_reader)  # skip the title row
            for i, row in enumerate(csv_reader, start=1):
                if str(i) in food_area_dictionary.keys():
                    # 第 5~10 column是六大營養指標的含量表
                    food_unit = food_area_dictionary[str(i)]/float(row[3])
                    # food_unit = 1 
                    # row[3]是單位重量的面積, 拿我們推估的實際面積去除以單位重量面積就是有多少份單位重量
                    # 舉例 : 白飯一單位重量定為100g, 單位重量面積測量約60cm^2, 現在有30cm^2的飯, 就有30/60=0.5單位重量的飯
                    for r in range(6):  #5碳水, 6脂肪, 7蛋白質, 8水, 9鉀, 10磷
                        nutrition_components[r] += float(row[5+r])*food_unit
                    # 第 11~14 column 是維生素
                    for r in range(4):  #11A, 12D, 13E, 14K
                        vitamines[r] += float(row[11+r])*food_unit
                    # 把食物 i 的面積加到它對應的第幾大類食物, 第一大類就加到 category_7_food[1-1](要-1因為沒有第0大類食物, 從1開始)
                    category_7_food[int(row[2])-1] += food_area_dictionary[str(i)]
                    row[3] = (food_unit*100)//1
                    detected_ingredients.append(row)
            print(f'componunents : {nutrition_components}')
            print(f'vitamines : {vitamines}')
            print(f'category_7_food : {category_7_food}')
        analysis_dict = {
            'ingerdients': detected_ingredients,
            'componunents': nutrition_components,
            'vitamines': vitamines,
            'category_7_food': category_7_food,
        }
        analysis_json = json.dumps(analysis_dict)
        request.session['analysis'] = analysis_json
        request.session['image_path'] = temp_image_path

        return JsonResponse({'success': True, 'username': username, 'detectedIngredients': detected_ingredients,
                             'components': nutrition_components, 'vitamines': vitamines, 'category_7_food': category_7_food})

    # return render(request, 'upload_form.html')

def save_user(request):
    if request.method == 'POST':
        form = EditInfoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        form = EditInfoForm(instance=request.user)
    # return render(request, 'update_profile.html', {'form': form})

def save_meal(request):
    if request.method == 'POST':
        username = request.user.username
        meal_data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static\\meal_data')
        meal_images_folder = os.path.join(meal_data_folder, 'meal_images')
        segmented_images_folder = os.path.join(meal_data_folder, 'segmented_images')
        save_time = timezone.now().strftime('%Y-%m-%d^%H-%M-%S')
        
        old_meal_image_save_name = os.path.join(meal_images_folder, f'{username}^temp.png')
        old_segmented_image_save_name = os.path.join(segmented_images_folder, f'{username}^temp.png')
        new_meal_image_save_name = os.path.join(meal_images_folder, f'{username}^{save_time}.png')
        new_segmented_image_save_name = os.path.join(segmented_images_folder, f'{username}^{save_time}.png')
        shutil.copy(old_meal_image_save_name, new_meal_image_save_name)
        shutil.copy(old_segmented_image_save_name, new_segmented_image_save_name)
        # os.rename(old_meal_image_save_name, new_meal_image_save_name)
        # os.rename(old_segmented_image_save_name, new_segmented_image_save_name)
        # image_path = request.session.get('image_path')
        # meal_image = request.FILES.get('meal_image')
        # segment_image = request.FILES.get('segment_image')
        # description = request.POST.get('description', '')  
        date_time = request.POST.get('date_time','')
        description = request.POST.get('description', '')  
        
        if new_meal_image_save_name:
            # Save meal data to the database
            meal = Meal(
                meal_image=new_meal_image_save_name,
                segment_image=new_segmented_image_save_name,
                analysis=request.session.get('analysis'),
                date_time=date_time,
                description=description,
                user=request.user,
            )
            meal.save()
            return JsonResponse({'success': True})  # Return a success response
        print("No image path passed to saveMeal()")
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})  # Return an error response for non-POST requests

def get_recent_meals(request):
    recent_meals = Meal.objects.filter(user_id=request.user.id).order_by('-date_time')[:4]
    data = {
        'recent_meals': [
            {
                'meal_image_url': meal.meal_image.url.split('/app')[1],
                'date_time': meal.date_time.strftime('%m/%d  %H:%M'),
                'description':"No description" if meal.description == "" else meal.description,
            }
            for meal in recent_meals
        ]
    }
    return JsonResponse(data)

def get_month_meals(request):
    current_date = timezone.now()
    meals = Meal.objects.filter(user=request.user, date_time__month=current_date.month)
    data = {
        'month_meals': [
            {
                'date_time': meal.date_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            for meal in meals
        ]
    }

    return JsonResponse(data)

def index(request):
    # return HttpResponse("Hello")
    return render(request, 'index.html')

def profile(request):
    return render(request, 'profile.html')

def save_movie_name(request, movie_name):
    m = Movie(movie_name=movie_name)
    m.save()
    return HttpResponse(movie_name + "is added")

def get_all_data(request):
    all_movies = Movie.objects.all()
    for movie in all_movies:
        print(movie.movie_name)
    return render(request, 'index.html', {'movies':all_movies})

def execute_docker_command():
    if INFERENCE_MODE == "demo":
        return

    host = _env("INFERENCE_SSH_HOST")
    port = int(_env("INFERENCE_SSH_PORT", "22"))
    username = _env("INFERENCE_SSH_USER")
    password = _env("INFERENCE_SSH_PASSWORD")

    # You can override the docker exec command via env var
    command = _env(
        "INFERENCE_DOCKER_COMMAND",
        'docker exec -i graduate2 bash -c "cd FoodSAM && python FoodSAM/semantic_v2.py --img_path dataset/uploaded_image.png --output dataset/test_output --data_root dataset/test_output"',
    )

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, port=port, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise RuntimeError(f"Remote inference failed: {stderr.read().decode(errors='ignore')}")
    finally:
        ssh.close()

def scp_upload(source_path):
    # Upload an image to the inference machine.
    # Credentials are provided via env vars; do NOT hardcode secrets.
    if INFERENCE_MODE == "demo":
        return

    host = _env("INFERENCE_SSH_HOST")
    port = int(_env("INFERENCE_SSH_PORT", "22"))
    username = _env("INFERENCE_SSH_USER")
    password = _env("INFERENCE_SSH_PASSWORD")
    destination_path = _env("INFERENCE_REMOTE_UPLOAD_PATH", "/tmp/uploaded_image.png")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, port=port, username=username, password=password)
        with ssh.open_sftp() as sftp:
            sftp.put(source_path, destination_path)
        execute_docker_command()
    finally:
        ssh.close()

def scp_download(segmented_image_destination, json_result_destination):
    # Download inference outputs from the inference machine (or use demo outputs).
    if INFERENCE_MODE == "demo":
        demo_dir = pathlib.Path(__file__).resolve().parent / "static" / "demo_outputs"
        demo_img = demo_dir / "enhance_vis.png"
        demo_json = demo_dir / "food_area.json"
        os.makedirs(os.path.dirname(segmented_image_destination), exist_ok=True)
        os.makedirs(os.path.dirname(json_result_destination), exist_ok=True)
        shutil.copyfile(demo_img, segmented_image_destination)
        shutil.copyfile(demo_json, json_result_destination)
        return

    host = _env("INFERENCE_SSH_HOST")
    port = int(_env("INFERENCE_SSH_PORT", "22"))
    username = _env("INFERENCE_SSH_USER")
    password = _env("INFERENCE_SSH_PASSWORD")

    segmented_image_source = _env(
        "INFERENCE_REMOTE_SEGMENTED_PATH",
        "/tmp/enhance_vis.png",
    )
    json_source = _env(
        "INFERENCE_REMOTE_JSON_PATH",
        "/tmp/food_area.json",
    )

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, port=port, username=username, password=password)
        with ssh.open_sftp() as sftp:
            sftp.get(segmented_image_source, segmented_image_destination)
            sftp.get(json_source, json_result_destination)
    finally:
        ssh.close()

