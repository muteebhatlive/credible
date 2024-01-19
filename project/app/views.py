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
            # Calculate approved limit using compound interest scheme
            monthly_salary = serializer.validated_data['monthly_income']
            approved_limit = round(36 * monthly_salary, -5)  # rounding to nearest lakh
            serializer.validated_data['approved_limit'] = approved_limit

            # Save the customer to the database
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_eligibility(request):
    print('CHECK ELIGIBILITY VIEW STARTS')
    serializer = EligibilityCheckSerializer(data=request.data)
    if serializer.is_valid():
        customer_id = serializer.validated_data['customer_id']
        loan_amount = serializer.validated_data['loan_amount']
        interest_rate = serializer.validated_data['interest_rate']
        tenure = serializer.validated_data['tenure']
        
    credit_score = calculate_credit_score(customer_id)
    approval, corrected_interest_rate, monthly_installment = check_loan_eligibility(loan_amount, interest_rate, tenure, credit_score)
    print('CREDIT SCORE RETRIEVED FROM FUNCTION: ', credit_score)
    print('APPROVAL RETRIEVED FROM FUNCTION: ', approval)
    print('CORRECTED INTEREST RATE RETRIEVED FROM FUNCTION: ', corrected_interest_rate)
    
    
    
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



def check_loan_eligibility(loan_amount, interest_rate, tenure, credit_score):
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
    print('started')
    credit_score = 100
    customer = Customer.objects.get(pk=customer_id)
    print('Customer', customer)
    loans = Loan.objects.filter(customer_id=customer_id)
    print('LOANS: ',loans)
    # on_time_payments = loans.filter(emis_paid_on_time=).count()
    current_date = datetime.now()
    print('1')
    print(current_date)
    print(type(current_date))
    current_date = current_date.date()
    current_date = current_date.strftime("%d-%m-%Y")
    print(current_date)
    print(type(current_date))
    date_object = datetime.strptime(current_date, "%d-%m-%Y").date()
    print(date_object)
    print(type(date_object))
    expired_loans = Loan.objects.filter(end_date__lt = date_object, customer_id=customer_id)
    print(expired_loans)
    for loans in expired_loans:
        if loans.tenure == loans.emis_paid_on_time:
            print('True', loans.end_date)
            credit_score += 20
            
        else: 
            print('False', loans.end_date)
            credit_score -= 20
            break 
    print('LOAN PAID ON TIME SCORE: ', credit_score)
    past_loans =  expired_loans.count()   
    print(past_loans)   
    credit_score -= past_loans * 17
    print('PAST LOANS SCORE: ',credit_score) # Adjust score based on on-time payments
    current_year = datetime.now().year
    current_year_loans = Loan.objects.filter(start_date__year=current_year).count()
    print(current_year_loans)
    credit_score -= current_year_loans * 10
    print('LOANS: ', loans)
    customer_loans = Loan.objects.filter(customer_id=customer_id)

    # Extract loan amounts into a list and calculate the total
    loan_amounts = [loan.loan_amount for loan in customer_loans]
    total_loan_amount = sum(loan_amounts)
    print('total: ', total_loan_amount)
    credit_score -= total_loan_amount / 1000000
    print('TOTAL LOAN: ',credit_score)
    if total_loan_amount > customer.approved_limit:
        credit_score = 0
        print('Higher Loan Amount Than Limit !!!', credit_score)
    else:
        print ('NOT Higher Loan Amount Than Limit: ', credit_score)
    credit_score = max(0, min(credit_score, 100))
    print(credit_score)
    return(credit_score)



@api_view(['POST'])
def create_loan(request):
    # Validate the request data
    serializer = EligibilityCheckSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Extract data from the serializer
    customer_id = serializer.validated_data['customer_id']
    loan_amount = serializer.validated_data['loan_amount']
    interest_rate = serializer.validated_data['interest_rate']
    tenure = serializer.validated_data['tenure']

    # Check loan eligibility
    approval, corrected_interest_rate, monthly_installment = check_loan_eligibility(
        loan_amount, interest_rate, tenure, customer_id
    )

    if not approval:
        # Loan is not approved
        response_data = {
            'loan_id': None,
            'customer_id': customer_id,
            'loan_approved': False,
            'message': 'Loan not approved. Check eligibility criteria.'
        }
        return Response(response_data, status=status.HTTP_200_OK)

    try:
        # Use get to fetch the customer without raising a 404 error
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        raise Http404("Customer does not exist")

    # Loan is approved, create a new Loan object and save it
    new_loan = Loan(
        customer_id=customer_id,
        loan_amount=loan_amount,
        interest_rate=corrected_interest_rate,
        tenure=tenure,
        monthly_payment=monthly_installment,
        emis_paid_on_time=0,  # Assuming no EMIs paid on time initially
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

    # Retrieve customer associated with the loan
    customer = Customer.objects.get(customer_id = loan.customer_id)
    # Serialize customer data
    customer_serializer = CustomerSerializer(customer)

    # Construct the response data
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