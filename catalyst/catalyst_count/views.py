from django.shortcuts import render,redirect,get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import serializers
from django.http import HttpResponse
from .serializers import SignupSerializer
from django.urls import reverse
from .tasks import process_upload
from django.core.files.storage import default_storage
import pandas as pd
from .models import Company
from rest_framework import status
from django.db.models import Q
from django.contrib.auth.models import User
from django.views import View
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

def home(request):
    return render(request, 'catalyst_count/home.html')

def login_page(request):
        return render(request, 'catalyst_count/login.html')

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class LoginView(APIView):
    permission_classes = [AllowAny]  # Allow anyone to access the login API

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                # Generate JWT token
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                home_url = reverse('upload_data') 

                # Return JWT tokens
                return Response({
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "redirect_url": home_url
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# --------- singUp Mechanism ---------
def signup_view(request):
    return render(request, 'catalyst_count/signup.html')

class SignupView(APIView):
    permission_classes = [AllowAny] 
    def post(self, request, *args, **kwargs):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
            return redirect('login_page')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# ---------- Users Mechanism
class UserListView(LoginRequiredMixin,View):
    # permission_classes = [AllowAny] 
    def get(self, request, *args, **kwargs):
            users_data = User.objects.all()  # Adjust this query as needed
            return render(request, 'catalyst_count/users.html', {'users': users_data})
@login_required
def delete_user(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        user.delete()  # Delete the user
        return redirect('users')  # Redirect to the user list page (replace 'user_list' with your actual URL name)
    except User.DoesNotExist:
        return HttpResponse("User not found.", status=404)

# ---------- File Upload
@login_required
def upload_data(request):
        return render(request, 'catalyst_count/upload_data.html')

class FileUploadView(LoginRequiredMixin,APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('csv_file')
        if not uploaded_file:
            return Response({'error': 'No file uploaded'}, status=400)
        
        file_path = default_storage.save(f'uploads/{uploaded_file.name}', uploaded_file)
        try:
            # Load the CSV file into a DataFrame
            data = pd.read_csv(file_path)
            # Normalize column names
            data.columns = (
                data.columns.str.strip()
                .str.lower()
                .str.replace(' ', '_')
                .str.replace('.', '_')
            )
            # Drop unwanted columns
            data = data.loc[:, ~data.columns.str.startswith('unnamed')]

            required_columns = {
                'name', 'domain', 'year_founded', 'industry', 'size_range',
                'locality', 'country', 'linkedin_url', 'current_employee_estimate', 'total_employee_estimate'
            }
            missing_columns = required_columns - set(data.columns)
            if missing_columns:
                return Response({'error': f'Missing required columns: {missing_columns}'}, status=400)

            # Process rows and save to database
            companies = []
            for _, row in data.iterrows():
                company = Company(
                    name=row['name'],
                    domain=row['domain'],
                    year_founded=int(str(row['year_founded']).replace(',', '').split('.')[0]),
                    industry=row['industry'],
                    size_range=row['size_range'],
                    locality=row['locality'],
                    country=row['country'],
                    linkedin_url=row['linkedin_url'],
                    current_employee_estimate=int(str(row['current_employee_estimate']).replace(',', '')) if not pd.isna(row['current_employee_estimate']) else None,
                    total_employee_estimate=int(str(row['total_employee_estimate']).replace(',', '')) if not pd.isna(row['total_employee_estimate']) else None
                )
                companies.append(company)

            # Bulk create in the database
            Company.objects.bulk_create(companies)

        except Exception as e:
            print(f"Error processing the file: {str(e)}")
            return Response({'error': 'Internal server error while processing the file'}, status=500)

        task = process_upload.apply_async(args=[file_path])
        return Response({'message': 'File uploaded successfully!', 'task_id': task.id})

# --------- Query builder 
@login_required
def query_builder(request):
        # Fetch distinct values from the Company table for each field
        industries = Company.objects.values_list('industry', flat=True).distinct()
        years_founded = Company.objects.values_list('year_founded', flat=True).distinct().order_by('-year_founded')
        countries = Company.objects.values_list('country', flat=True).distinct()
        
        context = {
            'industries': industries,
            'years_founded': years_founded,
            'countries': countries,
        }

        return render(request, 'catalyst_count/query_builder.html', context)


class QueryDataView(LoginRequiredMixin,APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        filters = request.data
        companies = Company.objects.all()

        # Apply filters based on the request data
        if filters.get('industry'):
            companies = companies.filter(industry=filters['industry'])
        if filters.get('year_founded'):
            companies = companies.filter(year_founded=filters['year_founded'])
        if filters.get('country'):
            companies = companies.filter(country=filters['country'])
        
        # Split the locality and filter by state or city
        if filters.get('state') or filters.get('city'):
            state_filter = filters.get('state')
            city_filter = filters.get('city')
            companies = companies.filter(
                Q(locality__icontains=city_filter) & Q(locality__icontains=state_filter)
            )
        elif filters.get('state'):
            state_filter = filters['state']
            companies = companies.filter(locality__icontains=state_filter)
        elif filters.get('city'):
            city_filter = filters['city']
            companies = companies.filter(locality__icontains=city_filter)

        # Get the count and results
        result_count = companies.distinct().count()
        results = []
        for company in companies.distinct():
            # Assuming locality is in the format "City, State"
            if ',' in company.locality:
                city, state = company.locality.split(',', 1)
                city = city.strip()
                state = state.strip()
            else:
                city = company.locality
                state = ''
            
            results.append({
                'name': company.name,
                'industry': company.industry,
                'year_founded': company.year_founded,
                'country': company.country,
                'state': state,
                'city': city,
                'linkedin_url': company.linkedin_url,
                'current_employee_estimate': company.current_employee_estimate,
                'total_employee_estimate': company.total_employee_estimate
            })
        return Response({
            'count': result_count,
            'results': results,
        })

class StateListView( LoginRequiredMixin, APIView):
    permission_classes = [AllowAny]
    def get(self, request, country, *args, **kwargs):
        # Extract states from the locality field
        states = Company.objects.filter(country=country).values_list('locality', flat=True)
        unique_states = set([locality.split(',')[-1].strip() for locality in states if ',' in locality])
        return Response({'states': list(unique_states)})

class CityListView(LoginRequiredMixin, APIView):
    permission_classes = [AllowAny]
    def get(self, request, state, *args, **kwargs):
        # Extract cities from the locality field
        cities = Company.objects.filter(locality__icontains=state).values_list('locality', flat=True)
        unique_cities = set([locality.split(',')[0].strip() for locality in cities if ',' in locality])
        return Response({'cities': list(unique_cities)})

def logout_view(request):
    logout(request)  # Logs out the user
    return redirect('login_page')  # Redirects to the login page (change this to your preferred page)




    

    
