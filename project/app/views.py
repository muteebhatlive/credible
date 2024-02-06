from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Customer, Loan
from .serializers import *
from datetime import datetime
from django.db.models import Sum    
from django.http import Http404
from dateutil.relativedelta import relativedelta

@api_view(['POST'])
def register(request):
    if request.method == 'POST':
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            monthly_salary = serializer.validated_data['monthly_salary']
            approved_limit = round(36 * monthly_salary) 
            serializer.validated_data['approved_limit'] = approved_limit
            customer = serializer.save()
            customer_id = customer.customer_id
            response_data = {
                "customer_id": customer_id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "age": customer.age,
                "monthly_salary": customer.monthly_salary,
                "phone_number": customer.phone_number,
                "approved_limit": customer.approved_limit,
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_eligibility(request):
    serializer = EligibilityCheckSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    customer_id = serializer.validated_data['customer_id']
    loan_amount = serializer.validated_data['loan_amount']
    interest_rate = serializer.validated_data['interest_rate']
    tenure = serializer.validated_data['tenure']
        
    credit_score = calculate_credit_score(customer_id)
    approval, corrected_interest_rate, monthly_installment = check_approval(loan_amount, interest_rate, tenure, credit_score)
    
    
    
    response_data = {
        "customer_id": customer_id,
        "credit_score" : credit_score,
        "approval": approval,
        "interest_rate": interest_rate,
        "corrected_interest_rate": corrected_interest_rate,
        "tenure": tenure,
        "monthly_installment": monthly_installment
    }

    return Response(response_data, status=status.HTTP_200_OK)



def check_approval(loan_amount, interest_rate, tenure, credit_score):
    credit_score =  int(credit_score)
    if credit_score > 50:
        approval = True
        corrected_interest_rate = interest_rate
    elif 50 >= credit_score > 30:
        approval = True
        corrected_interest_rate = max(interest_rate, 12)
    elif 30 >= credit_score > 10:
        approval = True
        corrected_interest_rate = max(interest_rate, 16)
    else:
        approval = False
        corrected_interest_rate = 0
    if approval == True:
        monthly_interest_rate = corrected_interest_rate / 100 / 12
        monthly_installment = (loan_amount * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** -tenure)
    else:
        monthly_installment = 0
    return approval, corrected_interest_rate, monthly_installment

def calculate_credit_score(customer_id):
    credit_score = 100
    customer = Customer.objects.get(pk=customer_id)
    loans = Loan.objects.filter(customer_id=customer_id)
    current_date = datetime.now()
    current_date = current_date.date()
    current_date = current_date.strftime("%d-%m-%Y")
    date_object = datetime.strptime(current_date, "%d-%m-%Y").date()
    expired_loans = Loan.objects.filter(end_date__lt = date_object, customer_id=customer_id)
    for loans in expired_loans:
        if loans.tenure == loans.emis_paid_on_time:
            credit_score += 20
            
        else: 
            credit_score -= 20
            break 
    past_loans =  expired_loans.count()   # Expired Loans in the past count
    credit_score -= past_loans * 17
    current_year = datetime.now().year
    current_year_loans = Loan.objects.filter(start_date__year=current_year).count()
    credit_score -= current_year_loans * 10
    customer_loans = Loan.objects.filter(customer_id=customer_id)
    loan_amounts = [loan.loan_amount for loan in customer_loans]
    total_loan_amount = sum(loan_amounts)
    credit_score -= total_loan_amount / 1000000
    if total_loan_amount > customer.approved_limit:
        credit_score = 0
    else:
        pass
    credit_score = max(0, min(credit_score, 100))
    return(credit_score)



@api_view(['POST'])
def create_loan(request):
    serializer = EligibilityCheckSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    customer_id = serializer.validated_data['customer_id']
    loan_amount = serializer.validated_data['loan_amount']
    interest_rate = serializer.validated_data['interest_rate']
    tenure = serializer.validated_data['tenure']

    # Check loan eligibility
    credit_score = calculate_credit_score(customer_id)
    approval, corrected_interest_rate, monthly_installment = check_approval(loan_amount, interest_rate, tenure, credit_score)

    if approval == False:
        # Loan is not approved
        response_data = {
            'loan_id': None,
            'customer_id': customer_id,
            'loan_approved': False,
            'message': 'Loan not approved. Check eligibility criteria.'
        }
        return Response(response_data, status=status.HTTP_200_OK)

    try:
        # Check for customer
        customer = Customer.objects.get(pk=customer_id)
    except:
        raise Http404("Customer does not exist")

    # Loan is approved, create a new Loan object and save it
    new_loan = Loan(
        customer_id=customer_id,
        loan_amount=loan_amount,
        interest_rate=corrected_interest_rate,
        tenure=tenure,
        monthly_payment=monthly_installment,
        emis_paid_on_time=0,  # Initial EMIs set to 0
        start_date=datetime.now().date(),
        end_date=datetime.now().date() + relativedelta(months=tenure)
    )
    
    new_loan.save()
    response_data = {
            'loan_id': new_loan.loan_id,
            'customer_id': customer_id,
            'loan_approved': True,
            'monthly_installment': monthly_installment
        }
    return Response(response_data,status=status.HTTP_201_CREATED)


@api_view(['GET'])
def view_loan(request, loan_id):
    try:
        loan = Loan.objects.get(loan_id=loan_id)
    except:
        return Response({"detail": "Loan not found"}, status=status.HTTP_404_NOT_FOUND)
    customer = Customer.objects.get(customer_id = loan.customer_id)

    customer_serializer = CustomerSerializer(customer)    # Serialize customer data
    response_data = {
        "loan_id": loan_id,
        "customer": customer_serializer.data,
        "loan_amount": loan.loan_amount,
        "interest_rate": loan.interest_rate,
        "monthly_installment": loan.monthly_payment,
        "tenure": loan.tenure,
    }

    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def view_loans_by_customer(request, customer_id):
    try:
        loans = Loan.objects.filter(customer_id=customer_id)
    except :
        return Response({"detail": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

    response_data = []
    for loan in loans:
        response_data.append({
            "loan_id": loan.loan_id,
            "loan_amount": loan.loan_amount,
            "interest_rate": loan.interest_rate,
            "monthly_installment": loan.monthly_payment,
            "repayments_left": loan.tenure - loan.emis_paid_on_time,
        })

    return Response(response_data, status=status.HTTP_200_OK)