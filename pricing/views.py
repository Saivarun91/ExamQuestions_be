from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import PricingPlan
import json


@api_view(['GET'])
def get_pricing_plans(request):
    """Get all active pricing plans (Public endpoint)"""
    try:
        plans = PricingPlan.objects(is_active=True).order_by('-is_popular', 'price')
        plans_data = []
        
        for plan in plans:
            plans_data.append({
                'id': str(plan.id),
                'name': plan.name,
                'price': plan.price,
                'currency': plan.currency,
                'currency_symbol': plan.currency_symbol,
                'duration_months': plan.duration_months,
                'duration_days': plan.duration_days,
                'original_price': plan.original_price,
                'discount_percentage': plan.discount_percentage,
                'per_day_cost': plan.per_day_cost,
                'features': plan.features,
                'color_scheme': plan.color_scheme,
                'is_popular': plan.is_popular,
                'pdf_enabled': plan.pdf_enabled,
                'pdf_price': plan.pdf_price,
                'is_active': plan.is_active,
                'created_at': plan.created_at.isoformat() if plan.created_at else None,
            })
        
        return Response({
            'success': True,
            'plans': plans_data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def admin_get_all_plans(request):
    """Get all pricing plans including inactive (Admin only)"""
    try:
        plans = PricingPlan.objects.all().order_by('display_order', '-is_popular', 'price')
        plans_data = []
        
        for plan in plans:
            plans_data.append({
                'id': str(plan.id),
                'name': plan.name,
                'price': plan.price,
                'currency': plan.currency,
                'currency_symbol': plan.currency_symbol,
                'duration_months': plan.duration_months,
                'duration_days': plan.duration_days,
                'original_price': plan.original_price,
                'discount_percentage': plan.discount_percentage,
                'per_day_cost': plan.per_day_cost,
                'features': plan.features,
                'color_scheme': plan.color_scheme,
                'is_popular': plan.is_popular,
                'pdf_enabled': plan.pdf_enabled,
                'pdf_price': plan.pdf_price,
                'is_active': plan.is_active,
                'display_order': getattr(plan, 'display_order', 0),
                'created_at': plan.created_at.isoformat() if plan.created_at else None,
            })
        
        return Response({
            'success': True,
            'plans': plans_data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def admin_create_plan(request):
    """Create a new pricing plan (Admin only)"""
    try:
        data = json.loads(request.body)
        
        plan = PricingPlan(
            name=data.get('name'),
            price=data.get('price'),
            currency=data.get('currency', 'INR'),
            currency_symbol=data.get('currency_symbol', '₹'),
            duration_months=data.get('duration_months', 1),
            duration_days=data.get('duration_days', 30),
            original_price=data.get('original_price', 0),
            discount_percentage=data.get('discount_percentage', 0),
            per_day_cost=data.get('per_day_cost', '0'),
            features=data.get('features', []),
            color_scheme=data.get('color_scheme', 'blue'),
            is_popular=data.get('is_popular', False),
            pdf_enabled=data.get('pdf_enabled', True),
            pdf_price=data.get('pdf_price', 0),
            is_active=data.get('is_active', True),
        )
        
        # Add display_order if present
        if 'display_order' in data:
            plan.display_order = data.get('display_order', 0)
        
        plan.save()
        
        return Response({
            'success': True,
            'message': 'Pricing plan created successfully',
            'plan_id': str(plan.id)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['PUT'])
def admin_update_plan(request, plan_id):
    """Update an existing pricing plan (Admin only)"""
    try:
        plan = PricingPlan.objects.get(id=plan_id)
        data = json.loads(request.body)
        
        # Update fields
        plan.name = data.get('name', plan.name)
        plan.price = data.get('price', plan.price)
        plan.currency = data.get('currency', plan.currency)
        plan.currency_symbol = data.get('currency_symbol', plan.currency_symbol)
        plan.duration_months = data.get('duration_months', plan.duration_months)
        plan.duration_days = data.get('duration_days', plan.duration_days)
        plan.original_price = data.get('original_price', plan.original_price)
        plan.discount_percentage = data.get('discount_percentage', plan.discount_percentage)
        plan.per_day_cost = data.get('per_day_cost', plan.per_day_cost)
        plan.features = data.get('features', plan.features)
        plan.color_scheme = data.get('color_scheme', plan.color_scheme)
        plan.is_popular = data.get('is_popular', plan.is_popular)
        plan.pdf_enabled = data.get('pdf_enabled', plan.pdf_enabled)
        plan.pdf_price = data.get('pdf_price', plan.pdf_price)
        plan.is_active = data.get('is_active', plan.is_active)
        
        if 'display_order' in data:
            plan.display_order = data.get('display_order', 0)
        
        plan.save()
        
        return Response({
            'success': True,
            'message': 'Pricing plan updated successfully'
        })
    except PricingPlan.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Pricing plan not found'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['DELETE'])
def admin_delete_plan(request, plan_id):
    """Delete a pricing plan (Admin only)"""
    try:
        plan = PricingPlan.objects.get(id=plan_id)
        plan.delete()
        
        return Response({
            'success': True,
            'message': 'Pricing plan deleted successfully'
        })
    except PricingPlan.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Pricing plan not found'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def admin_initialize_plans(request):
    """Initialize default pricing plans (Admin only)"""
    try:
        # Import and run the initialization
        from pricing.init_pricing_data import init_pricing_data
        plans = init_pricing_data()
        
        return Response({
            'success': True,
            'message': f'Successfully initialized {len(plans)} pricing plans'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

