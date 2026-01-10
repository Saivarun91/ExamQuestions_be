import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date
from .models import Lead
from bson import ObjectId
from common.middleware import authenticate, restrict

@csrf_exempt
def submit_lead(request):
    """
    Public API: Submit a lead/inquiry form.
    No authentication required - anyone can submit.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone_number = data.get("phone_number", "").strip()
        whatsapp_number = data.get("whatsapp_number", "").strip()
        course = data.get("course", "").strip()
        course_id = data.get("course_id", "")
        search_query = data.get("search_query", "").strip()

        # Validate required fields
        if not name or not email or not whatsapp_number:
            return JsonResponse({
                "success": False,
                "message": "Name, email, and WhatsApp number are required"
            }, status=400)

        # Get IP address and user agent
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or \
                    request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Create lead
        lead = Lead(
            name=name,
            email=email,
            phone_number=phone_number if phone_number else None,
            whatsapp_number=whatsapp_number,
            course=course if course else "General Inquiry",
            course_id=course_id if course_id else None,
            search_query=search_query if search_query else None,
            ip_address=ip_address,
            user_agent=user_agent,
            status='new'
        )
        lead.save()

        return JsonResponse({
            "success": True,
            "message": "Thank you! Our team will contact you soon.",
            "lead_id": str(lead.id)
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        import traceback
        print(f"Error in submit_lead: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def get_leads(request):
    """
    Admin API: Get all leads with filtering options.
    Includes enrollment status checking by email and phone.
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        from users.models import User
        from enrollments.models import Enrollment
        
        # Get filter parameters
        status_filter = request.GET.get("status", None)
        
        # Build query
        query = {}
        if status_filter:
            query["status"] = status_filter

        leads = Lead.objects(**query).order_by('-created_at')

        leads_data = []
        for lead in leads:
            # Check if user enrolled by email or phone
            enrolled = False
            enrollment_info = None
            
            # Try to find user by email
            user = None
            try:
                user = User.objects(email=lead.email.lower()).first()
            except:
                pass
            
            # If no user by email, try by phone (if stored in user model)
            if not user and lead.whatsapp_number:
                try:
                    user = User.objects(phone_number=lead.whatsapp_number).first()
                except:
                    pass
            
            # If user found, check enrollments
            if user:
                try:
                    enrollments = Enrollment.objects(user_name=str(user.id))
                    if enrollments:
                        enrolled = True
                        # Get most recent enrollment
                        latest_enrollment = enrollments.order_by('-enrolled_date').first()
                        if latest_enrollment:
                            course_name = None
                            if latest_enrollment.course:
                                course_name = latest_enrollment.course.name if hasattr(latest_enrollment.course, 'name') else str(latest_enrollment.course)
                            elif latest_enrollment.category:
                                course_name = latest_enrollment.category.name if hasattr(latest_enrollment.category, 'name') else str(latest_enrollment.category)
                            
                            enrollment_info = {
                                "course_name": course_name or "Unknown",
                                "enrolled_date": latest_enrollment.enrolled_date.isoformat() if latest_enrollment.enrolled_date else None,
                                "expiry_date": latest_enrollment.expiry_date.isoformat() if latest_enrollment.expiry_date else None,
                                "status": "active" if (latest_enrollment.expiry_date and latest_enrollment.expiry_date >= date.today()) else "expired"
                            }
                except Exception as e:
                    print(f"Error checking enrollment for lead {lead.id}: {e}")
            
            leads_data.append({
                "id": str(lead.id),
                "name": lead.name,
                "email": lead.email,
                "phone_number": lead.phone_number or None,
                "whatsapp_number": lead.whatsapp_number,
                "course": lead.course,
                "course_id": lead.course_id or None,
                "search_query": lead.search_query or None,
                "status": lead.status,
                "notes": lead.notes or "",
                "contacted_at": lead.contacted_at.isoformat() if lead.contacted_at else None,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "ip_address": lead.ip_address or None,
                "is_enrolled": enrolled,
                "enrollment_info": enrollment_info,
            })

        return JsonResponse({
            "success": True,
            "leads": leads_data,
            "total": len(leads_data)
        }, status=200)

    except Exception as e:
        import traceback
        print(f"Error in get_leads: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def update_lead_status(request, lead_id):
    """
    Admin API: Update lead status and add notes.
    """
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(lead_id):
            return JsonResponse({"success": False, "message": "Invalid lead ID"}, status=400)

        data = json.loads(request.body)
        lead = Lead.objects.get(pk=ObjectId(lead_id))

        # Update status if provided
        if "status" in data:
            new_status = data["status"]
            if new_status in ['new', 'contacted', 'converted', 'closed']:
                lead.status = new_status
                if new_status == 'contacted':
                    lead.contacted_at = datetime.utcnow()

        # Update notes if provided
        if "notes" in data:
            lead.notes = data["notes"].strip()

        lead.updated_at = datetime.utcnow()
        lead.save()

        return JsonResponse({
            "success": True,
            "message": "Lead updated successfully"
        }, status=200)

    except Lead.DoesNotExist:
        return JsonResponse({"success": False, "message": "Lead not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in update_lead_status: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def delete_lead(request, lead_id):
    """
    Admin API: Delete a lead.
    """
    if request.method != "DELETE":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(lead_id):
            return JsonResponse({"success": False, "message": "Invalid lead ID"}, status=400)

        lead = Lead.objects.get(pk=ObjectId(lead_id))
        lead.delete()

        return JsonResponse({
            "success": True,
            "message": "Lead deleted successfully"
        }, status=200)

    except Lead.DoesNotExist:
        return JsonResponse({"success": False, "message": "Lead not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in delete_lead: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)

