from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from modules.jobs.models import TinTuyenDung
from modules.candidate_matching.models import JobPersonalityRequirement, CandidatePersonalityProfile
from modules.candidate_matching.serializers import (
    JobMatchingResultSerializer,
    JobPersonalityRequirementSerializer,
    CandidatePersonalityProfileSerializer,
)
from modules.candidate_matching.services import JobMatchingService


class JobMatchingViewSet(viewsets.ViewSet):
    """
    API ViewSet cho tìm kiếm ứng viên phù hợp
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Tìm ứng viên phù hợp cho công việc',
        tags=['candidate-matching'],
        parameters=[
            OpenApiParameter(
                name='job_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='ID của công việc cần tìm ứng viên'
            ),
        ],
        responses={200: JobMatchingResultSerializer},
    )
    @action(detail=False, methods=['get'], url_path='jobs/(?P<job_id>[^/.]+)')
    def find_candidates_for_job(self, request, job_id=None):
        """
        Tìm ứng viên phù hợp cho một công việc cụ thể
        
        Thuật toán:
        - Điểm kỹ năng: Kiểm tra chuyên ngành match + kỹ năng match
        - Điểm tính cách: So sánh 80% đặc điểm tính cách yêu cầu
        - Điểm tổng: 40% kỹ năng + 60% tính cách
        - Eligible: Kỹ năng ≥ 30% AND Tính cách ≥ 80%
        """
        try:
            job = TinTuyenDung.objects.get(tin_id=job_id)
        except TinTuyenDung.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Run matching algorithm
        matching_service = JobMatchingService(job)
        result = matching_service.find_matching_candidates()
        
        # Prepare response
        candidates_data = []
        for match in result['matching_candidates']:
            candidate = match['candidate']
            candidates_data.append({
                'ung_vien_id': candidate.ung_vien_id,
                'ho_ten': candidate.ho_ten,
                'avatar': candidate.avatar,
                'ky_nang': candidate.ky_nang,
                'vi_tri_mong_muon': candidate.vi_tri_mong_muon,
                'location': candidate.location,
                'luong_mong_muon': candidate.luong_mong_muon,
                'skill_match_score': match['skill_score'],
                'personality_match_score': match['personality_score'],
                'overall_match_score': match['overall_score'],
                'matched_skills': match['matched_skills'],
                'matched_traits': match['matched_traits'],
            })
        
        response_data = {
            'job_id': job.tin_id,
            'job_title': job.tieu_de,
            'company_name': job.cong_ty.ten_cong_ty,
            'total_candidates': result['total_candidates'],
            'eligible_candidates': result['eligible_count'],
            'candidates': candidates_data,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(
        summary='Lấy danh sách ứng viên phù hợp nhất (eligible)',
        tags=['candidate-matching'],
        parameters=[
            OpenApiParameter(
                name='job_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='ID của công việc'
            ),
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Số lượng ứng viên trả về (default: 10)'
            ),
        ],
        responses={200: JobMatchingResultSerializer},
    )
    @action(detail=False, methods=['get'], url_path='jobs/(?P<job_id>[^/.]+)/eligible-candidates')
    def get_eligible_candidates(self, request, job_id=None):
        """
        Lấy danh sách ứng viên eligible (phù hợp nhất)
        - Kỹ năng ≥ 30% AND Tính cách ≥ 80%
        """
        try:
            job = TinTuyenDung.objects.get(tin_id=job_id)
        except TinTuyenDung.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        limit = int(request.query_params.get('limit', 10))
        
        # Run matching algorithm
        matching_service = JobMatchingService(job)
        result = matching_service.find_matching_candidates()
        
        # Filter only eligible
        eligible_matches = [m for m in result['matching_candidates'] if m['is_eligible']][:limit]
        
        candidates_data = []
        for match in eligible_matches:
            candidate = match['candidate']
            candidates_data.append({
                'ung_vien_id': candidate.ung_vien_id,
                'ho_ten': candidate.ho_ten,
                'avatar': candidate.avatar,
                'ky_nang': candidate.ky_nang,
                'vi_tri_mong_muon': candidate.vi_tri_mong_muon,
                'location': candidate.location,
                'luong_mong_muon': candidate.luong_mong_muon,
                'skill_match_score': match['skill_score'],
                'personality_match_score': match['personality_score'],
                'overall_match_score': match['overall_score'],
                'matched_skills': match['matched_skills'],
                'matched_traits': match['matched_traits'],
            })
        
        response_data = {
            'job_id': job.tin_id,
            'job_title': job.tieu_de,
            'company_name': job.cong_ty.ten_cong_ty,
            'total_candidates': result['total_candidates'],
            'eligible_candidates': len(candidates_data),
            'candidates': candidates_data,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class JobPersonalityRequirementViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints cho yêu cầu đặc điểm tính cách công việc
    """
    permission_classes = [IsAuthenticated]
    queryset = JobPersonalityRequirement.objects.all()
    serializer_class = JobPersonalityRequirementSerializer
    lookup_field = 'tin_id'

    @extend_schema(
        summary='Tạo/Cập nhật yêu cầu tính cách cho công việc',
        tags=['candidate-matching'],
    )
    def create(self, request, *args, **kwargs):
        """Tạo hoặc cập nhật yêu cầu tính cách"""
        tin_id = request.data.get('tin_id')
        
        try:
            job = TinTuyenDung.objects.get(tin_id=tin_id)
        except TinTuyenDung.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        requirement, created = JobPersonalityRequirement.objects.update_or_create(
            tin=job,
            defaults={'traits_required': request.data.get('traits_required', [])}
        )
        
        serializer = self.get_serializer(requirement)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class CandidatePersonalityProfileViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints cho hồ sơ tính cách của ứng viên
    """
    permission_classes = [IsAuthenticated]
    queryset = CandidatePersonalityProfile.objects.all()
    serializer_class = CandidatePersonalityProfileSerializer
    lookup_field = 'ung_vien_id'

    @extend_schema(
        summary='Tạo/Cập nhật hồ sơ tính cách của ứng viên',
        tags=['candidate-matching'],
    )
    def create(self, request, *args, **kwargs):
        """Tạo hoặc cập nhật hồ sơ tính cách"""
        from modules.profiles.models import HoSoUngVien
        
        ung_vien_id = request.data.get('ung_vien_id')
        
        try:
            candidate = HoSoUngVien.objects.get(ung_vien_id=ung_vien_id)
        except HoSoUngVien.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        profile, created = CandidatePersonalityProfile.objects.update_or_create(
            ung_vien=candidate,
            defaults={
                'traits_profile': request.data.get('traits_profile', []),
                'niche': request.data.get('niche', ''),
            }
        )
        
        serializer = self.get_serializer(profile)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
