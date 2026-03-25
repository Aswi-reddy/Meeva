from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from vendor.emails import (
    send_vendor_approval_email,
    send_vendor_reactivation_email,
    send_vendor_rejection_email,
    send_vendor_suspension_email,
)
from vendor.models import Vendor

from .permissions import IsCoreAdminUser
from .serializers import (
    AdminVendorDetailSerializer,
    AdminVendorListSerializer,
    AdminVendorRejectSerializer,
)


class AdminDashboardView(APIView):
    permission_classes = [IsCoreAdminUser]

    def get(self, request):
        pending_count = Vendor.objects.filter(status='pending').count()
        approved_count = Vendor.objects.filter(status='approved').count()
        rejected_count = Vendor.objects.filter(status='rejected').count()
        suspended_count = Vendor.objects.filter(status='suspended').count()
        total_vendors = Vendor.objects.count()

        admin = request.user.meeva_core_admin
        return Response({
            'admin': {
                'id': admin.id,
                'email': admin.email,
            },
            'vendor_stats': {
                'pending_count': pending_count,
                'approved_count': approved_count,
                'rejected_count': rejected_count,
                'suspended_count': suspended_count,
                'total_vendors': total_vendors,
            },
        })


class AdminVendorsView(APIView):
    permission_classes = [IsCoreAdminUser]

    def get(self, request):
        status_filter = (request.GET.get('status') or 'all').strip()

        qs = Vendor.objects.all().order_by('-created_at')
        if status_filter != 'all':
            qs = qs.filter(status=status_filter)

        return Response({
            'status_filter': status_filter,
            'vendors': AdminVendorListSerializer(qs, many=True, context={'request': request}).data,
        })


class AdminPendingVendorsView(APIView):
    permission_classes = [IsCoreAdminUser]

    def get(self, request):
        qs = Vendor.objects.filter(status='pending').order_by('-created_at')
        return Response({
            'vendors': AdminVendorListSerializer(qs, many=True, context={'request': request}).data,
        })


class AdminVendorDetailView(APIView):
    permission_classes = [IsCoreAdminUser]

    def get(self, request, vendor_id: int):
        vendor = Vendor.objects.filter(id=vendor_id).first()
        if not vendor:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(AdminVendorDetailSerializer(vendor, context={'request': request}).data)


class AdminVendorApproveView(APIView):
    permission_classes = [IsCoreAdminUser]

    def post(self, request, vendor_id: int):
        vendor = Vendor.objects.filter(id=vendor_id).first()
        if not vendor:
            return Response({'detail': 'Not found.'}, status=404)

        admin_email = request.user.meeva_core_admin.email

        vendor.status = 'approved'
        vendor.approved_by = admin_email
        vendor.approved_at = timezone.now()
        vendor.rejection_reason = None
        vendor.save()

        email_sent = send_vendor_approval_email(vendor, admin_email)

        return Response({
            'email_sent': bool(email_sent),
            'vendor': AdminVendorDetailSerializer(vendor, context={'request': request}).data,
        })


class AdminVendorRejectView(APIView):
    permission_classes = [IsCoreAdminUser]

    def post(self, request, vendor_id: int):
        vendor = Vendor.objects.filter(id=vendor_id).first()
        if not vendor:
            return Response({'detail': 'Not found.'}, status=404)

        serializer = AdminVendorRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rejection_reason = (serializer.validated_data.get('rejection_reason') or 'No reason provided').strip() or 'No reason provided'

        vendor.status = 'rejected'
        vendor.rejection_reason = rejection_reason
        vendor.save()

        email_sent = send_vendor_rejection_email(vendor, rejection_reason)

        return Response({
            'email_sent': bool(email_sent),
            'vendor': AdminVendorDetailSerializer(vendor, context={'request': request}).data,
        })


class AdminVendorSuspendView(APIView):
    permission_classes = [IsCoreAdminUser]

    def post(self, request, vendor_id: int):
        vendor = Vendor.objects.filter(id=vendor_id).first()
        if not vendor:
            return Response({'detail': 'Not found.'}, status=404)

        vendor.status = 'suspended'
        vendor.is_active = False
        vendor.save()

        email_sent = send_vendor_suspension_email(vendor)

        return Response({
            'email_sent': bool(email_sent),
            'vendor': AdminVendorDetailSerializer(vendor, context={'request': request}).data,
        })


class AdminVendorActivateView(APIView):
    permission_classes = [IsCoreAdminUser]

    def post(self, request, vendor_id: int):
        vendor = Vendor.objects.filter(id=vendor_id).first()
        if not vendor:
            return Response({'detail': 'Not found.'}, status=404)

        vendor.status = 'approved'
        vendor.is_active = True
        vendor.save()

        email_sent = send_vendor_reactivation_email(vendor)

        return Response({
            'email_sent': bool(email_sent),
            'vendor': AdminVendorDetailSerializer(vendor, context={'request': request}).data,
        })
