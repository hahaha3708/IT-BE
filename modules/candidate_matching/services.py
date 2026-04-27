"""
Service cho job matching algorithm
Thuật toán: Tìm ứng viên phù hợp theo:
1. Chuyên ngành/kỹ năng (skill matching)
2. 80% đặc điểm tính cách công ty yêu cầu (personality matching)
"""

from difflib import SequenceMatcher
from typing import List, Dict, Tuple
from django.db.models import Q
from modules.jobs.models import TinTuyenDung
from modules.profiles.models import HoSoUngVien
from modules.candidate_matching.models import JobPersonalityRequirement, CandidatePersonalityProfile


class JobMatchingService:
    """Service xử lý thuật toán matching ứng viên"""
    
    SKILL_MATCH_THRESHOLD = 0.3  # 30% match skills được coi là phù hợp
    PERSONALITY_MATCH_THRESHOLD = 0.8  # 80% match tính cách
    OVERALL_MATCH_THRESHOLD = 0.6  # 60% overall match để được coi là eligible

    def __init__(self, job: TinTuyenDung):
        self.job = job
        self.job_requirements = self._parse_job_requirements(job)
        self.personality_requirement = self._get_personality_requirement(job)

    def _parse_job_requirements(self, job: TinTuyenDung) -> Dict:
        """Parse yêu cầu công việc từ text"""
        return {
            'title': job.tieu_de.lower(),
            'requirements_text': (job.yeu_cau or '').lower(),
            'niche': self._extract_niche(job.tieu_de),
        }

    def _extract_niche(self, job_title: str) -> str:
        """Trích xuất chuyên ngành từ tiêu đề công việc"""
        job_title_lower = job_title.lower()
        
        # Danh sách từ khóa cho từng chuyên ngành
        niche_keywords = {
            'backend': ['backend', 'server', 'api', 'database', 'python', 'java', 'nodejs'],
            'frontend': ['frontend', 'ui', 'ux', 'react', 'vue', 'angular', 'javascript'],
            'fullstack': ['fullstack', 'full-stack', 'full stack'],
            'devops': ['devops', 'infrastructure', 'docker', 'kubernetes', 'ci/cd'],
            'mobile': ['mobile', 'ios', 'android', 'flutter', 'react native'],
            'data': ['data', 'analytics', 'ml', 'ai', 'machine learning'],
            'qa': ['qa', 'test', 'quality assurance', 'automation'],
        }
        
        for niche, keywords in niche_keywords.items():
            if any(kw in job_title_lower for kw in keywords):
                return niche
        
        return 'other'

    def _get_personality_requirement(self, job: TinTuyenDung) -> List[Dict]:
        """Lấy yêu cầu đặc điểm tính cách từ database"""
        try:
            req = JobPersonalityRequirement.objects.get(tin=job)
            return req.traits_required if req.traits_required else []
        except JobPersonalityRequirement.DoesNotExist:
            # Nếu chưa có yêu cầu tính cách, dùng default
            return self._get_default_traits()

    def _get_default_traits(self) -> List[Dict]:
        """Default traits cho job matching"""
        return [
            {"name": "teamwork", "weight": 0.2},
            {"name": "proactive", "weight": 0.15},
            {"name": "problem_solving", "weight": 0.25},
            {"name": "communication", "weight": 0.2},
            {"name": "responsibility", "weight": 0.2}
        ]

    def calculate_skill_match(self, candidate: HoSoUngVien) -> Tuple[float, List[str]]:
        """
        Tính điểm match kỹ năng
        - Nếu chuyên ngành match: 70% điểm
        - Nếu kỹ năng match: +30% điểm
        """
        score = 0.0
        matched_skills = []
        
        # Check niche match
        try:
            candidate_profile = CandidatePersonalityProfile.objects.get(ung_vien=candidate)
            candidate_niche = (candidate_profile.niche or '').lower()
        except CandidatePersonalityProfile.DoesNotExist:
            candidate_niche = (candidate.vi_tri_mong_muon or '').lower()
        
        job_niche = self.job_requirements['niche']
        
        # Niche matching (70% of skill score)
        if candidate_niche and self._string_similarity(candidate_niche, job_niche) > 0.3:
            score += 0.7
            matched_skills.append(f"Chuyên ngành: {candidate_niche}")
        
        # Skills matching (30% of skill score)
        candidate_skills = (candidate.ky_nang or '').lower().split(',')
        job_requirements = self.job_requirements['requirements_text'].split(',')
        
        skill_matches = 0
        for req in job_requirements:
            for skill in candidate_skills:
                if self._string_similarity(skill.strip(), req.strip()) > 0.5:
                    skill_matches += 1
                    matched_skills.append(skill.strip())
                    break
        
        if job_requirements:
            skill_ratio = min(skill_matches / len(job_requirements), 1.0)
            score += skill_ratio * 0.3
        
        return min(score, 1.0), matched_skills

    def calculate_personality_match(self, candidate: HoSoUngVien) -> Tuple[float, List[Dict]]:
        """
        Tính điểm match tính cách
        So sánh traits của ứng viên với traits yêu cầu
        """
        try:
            candidate_profile = CandidatePersonalityProfile.objects.get(ung_vien=candidate)
            candidate_traits = candidate_profile.traits_profile
        except CandidatePersonalityProfile.DoesNotExist:
            # Nếu chưa có profile tính cách, dùng default
            candidate_traits = self._get_default_candidate_traits()
        
        # Tạo dict từ candidate traits
        candidate_trait_dict = {}
        if candidate_traits:
            for trait in candidate_traits:
                candidate_trait_dict[trait.get('name')] = trait.get('score', 0.5)
        
        # Calculate weighted score
        total_weight = 0
        weighted_score = 0
        matched_traits = []
        
        for req_trait in self.personality_requirement:
            trait_name = req_trait.get('name')
            trait_weight = req_trait.get('weight', 1.0)
            
            candidate_score = candidate_trait_dict.get(trait_name, 0.5)  # Default 0.5 if not found
            
            total_weight += trait_weight
            weighted_score += candidate_score * trait_weight
            
            if candidate_score >= 0.6:  # 60% trở lên coi là match
                matched_traits.append({
                    'name': trait_name,
                    'score': candidate_score,
                    'weight': trait_weight
                })
        
        overall_personality_score = weighted_score / total_weight if total_weight > 0 else 0
        
        return min(overall_personality_score, 1.0), matched_traits

    def _get_default_candidate_traits(self) -> List[Dict]:
        """Default traits cho ứng viên nếu chưa có profile"""
        return [
            {"name": "teamwork", "score": 0.5},
            {"name": "proactive", "score": 0.5},
            {"name": "problem_solving", "score": 0.5},
            {"name": "communication", "score": 0.5},
            {"name": "responsibility", "score": 0.5}
        ]

    def _string_similarity(self, str1: str, str2: str) -> float:
        """Tính độ tương tự giữa 2 chuỗi"""
        return SequenceMatcher(None, str1.strip(), str2.strip()).ratio()

    def find_matching_candidates(self) -> Dict:
        """Tìm tất cả ứng viên phù hợp với job"""
        all_candidates = HoSoUngVien.objects.all()
        
        matching_candidates = []
        
        for candidate in all_candidates:
            skill_score, matched_skills = self.calculate_skill_match(candidate)
            personality_score, matched_traits = self.calculate_personality_match(candidate)
            
            # Overall score: 40% skill + 60% personality
            overall_score = (skill_score * 0.4) + (personality_score * 0.6)
            
            # Kiểm tra điều kiện đủ điều kiện
            is_eligible = (skill_score >= self.SKILL_MATCH_THRESHOLD and 
                          personality_score >= self.PERSONALITY_MATCH_THRESHOLD)
            
            if is_eligible or overall_score >= self.OVERALL_MATCH_THRESHOLD:
                matching_candidates.append({
                    'candidate': candidate,
                    'skill_score': round(skill_score, 2),
                    'personality_score': round(personality_score, 2),
                    'overall_score': round(overall_score, 2),
                    'matched_skills': matched_skills,
                    'matched_traits': matched_traits,
                    'is_eligible': is_eligible,
                })
        
        # Sort by overall score
        matching_candidates.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Count eligible
        eligible_count = sum(1 for c in matching_candidates if c['is_eligible'])
        
        return {
            'job': self.job,
            'total_candidates': len(all_candidates),
            'matching_candidates': matching_candidates,
            'eligible_count': eligible_count,
        }
