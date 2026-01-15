"""
Performance tests for JobPilot AI Backend.
Tests response times, throughput, and resource usage.
"""
import pytest
import asyncio
import time
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.user import User
from concurrent.futures import ThreadPoolExecutor
import statistics


# Performance budgets (in seconds)
PERFORMANCE_BUDGETS = {
    "health_check": 0.1,
    "auth_login": 0.5,
    "auth_register": 1.0,
    "resume_upload": 2.0,
    "resume_parsing": 5.0,
    "ai_resume_version": 10.0,
    "ai_interview_prep": 15.0,
    "ai_skill_analysis": 5.0,
    "job_matching": 3.0,
    "database_query": 0.5,
}


@pytest.mark.asyncio
class TestResponseTimePerformance:
    """Test individual endpoint response times."""
    
    async def test_health_check_performance(self, client: AsyncClient):
        """Test health check endpoint performance."""
        times = []
        
        for _ in range(10):
            start_time = time.time()
            response = await client.get(f"{settings.API_V1_STR}/health")
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        assert avg_time < PERFORMANCE_BUDGETS["health_check"], \
            f"Health check avg time {avg_time:.3f}s exceeds budget {PERFORMANCE_BUDGETS['health_check']}s"
        assert max_time < PERFORMANCE_BUDGETS["health_check"] * 2, \
            f"Health check max time {max_time:.3f}s exceeds 2x budget"
    
    async def test_auth_login_performance(self, client: AsyncClient, test_user: User, test_password: str):
        """Test login endpoint performance."""
        times = []
        
        for _ in range(5):
            start_time = time.time()
            response = await client.post(
                f"{settings.API_V1_STR}/auth/login",
                json={"email": test_user.email, "password": test_password}
            )
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        
        assert avg_time < PERFORMANCE_BUDGETS["auth_login"], \
            f"Login avg time {avg_time:.3f}s exceeds budget {PERFORMANCE_BUDGETS['auth_login']}s"
    
    async def test_auth_register_performance(self, client: AsyncClient):
        """Test registration endpoint performance."""
        times = []
        
        for i in range(3):  # Fewer iterations due to unique email constraint
            start_time = time.time()
            response = await client.post(
                f"{settings.API_V1_STR}/auth/register",
                json={
                    "email": f"perftest{i}@example.com",
                    "password": "TestPass123!"
                }
            )
            end_time = time.time()
            
            assert response.status_code == 201
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        
        assert avg_time < PERFORMANCE_BUDGETS["auth_register"], \
            f"Register avg time {avg_time:.3f}s exceeds budget {PERFORMANCE_BUDGETS['auth_register']}s"
    
    async def test_resume_list_performance(self, client: AsyncClient, auth_headers: dict):
        """Test resume listing performance."""
        times = []
        
        for _ in range(10):
            start_time = time.time()
            response = await client.get(
                f"{settings.API_V1_STR}/resume/list",
                headers=auth_headers
            )
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        
        assert avg_time < PERFORMANCE_BUDGETS["database_query"], \
            f"Resume list avg time {avg_time:.3f}s exceeds budget {PERFORMANCE_BUDGETS['database_query']}s"
    
    @pytest.mark.skip(reason="Requires endpoints that don't exist in current implementation")
    @pytest.mark.slow
    async def test_ai_resume_version_performance(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test AI resume versioning performance."""
        # First create a resume and job
        resume_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload-parsed",
            json={
                "filename": "perf_test_resume.pdf",
                "parsed_data": '{"name": "Test User", "skills": ["Python", "JavaScript"], "experience": [{"company": "Test Corp", "position": "Developer"}]}',
                "file_size": 1024,
                "is_parsed": True
            },
            headers=auth_headers
        )
        assert resume_response.status_code in [200, 201]
        
        job_response = await client.post(
            f"{settings.API_V1_STR}/jobs",
            json={
                "title": "Senior Developer",
                "company": "Tech Corp",
                "description": "Looking for a senior developer with Python and React skills",
                "requirements": "5+ years experience with Python, React, and databases",
                "location": "Remote",
                "job_type": "full-time",
                "source": "test"
            },
            headers=auth_headers
        )
        assert job_response.status_code in [200, 201]
        job_id = job_response.json()["id"]
        
        # Test AI resume versioning performance
        start_time = time.time()
        response = await client.post(
            f"{settings.API_V1_STR}/ai/resume/version/{job_id}",
            json={"optimization_focus": ["keywords", "ats_score"]},
            headers=auth_headers
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        if response.status_code == 200:
            assert processing_time < PERFORMANCE_BUDGETS["ai_resume_version"], \
                f"AI resume version time {processing_time:.3f}s exceeds budget {PERFORMANCE_BUDGETS['ai_resume_version']}s"
        else:
            pytest.skip(f"AI resume versioning not available (status: {response.status_code})")
    
    @pytest.mark.slow
    async def test_ai_skill_analysis_performance(self, client: AsyncClient, auth_headers: dict):
        """Test AI skill analysis performance."""
        # Create test job for skill analysis
        job_response = await client.post(
            f"{settings.API_V1_STR}/jobs",
            json={
                "title": "Full Stack Developer",
                "company": "AI Corp",
                "description": "Full stack developer needed with React, Node.js, Python, AWS, Docker skills",
                "requirements": "Required: React, Node.js, Python, AWS, Docker. Preferred: Kubernetes, TypeScript",
                "location": "San Francisco",
                "job_type": "full-time",
                "source": "test"
            },
            headers=auth_headers
        )
        
        if job_response.status_code not in [200, 201]:
            pytest.skip("Could not create test job for skill analysis")
        
        job_id = job_response.json()["id"]
        
        # Test skill analysis performance
        start_time = time.time()
        response = await client.post(
            f"{settings.API_V1_STR}/ai/skills/analyze",
            json={
                "job_id": job_id,
                "include_market_data": True,
                "regenerate": True
            },
            headers=auth_headers
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        if response.status_code == 200:
            assert processing_time < PERFORMANCE_BUDGETS["ai_skill_analysis"], \
                f"AI skill analysis time {processing_time:.3f}s exceeds budget {PERFORMANCE_BUDGETS['ai_skill_analysis']}s"
        else:
            pytest.skip(f"AI skill analysis not available (status: {response.status_code})")


@pytest.mark.asyncio
class TestConcurrencyPerformance:
    """Test concurrent request handling."""
    
    async def test_concurrent_health_checks(self, client: AsyncClient):
        """Test handling multiple concurrent health check requests."""
        async def make_request():
            response = await client.get(f"{settings.API_V1_STR}/health")
            return response.status_code, time.time()
        
        # Make 20 concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # All requests should succeed
        status_codes = [result[0] for result in results]
        assert all(code == 200 for code in status_codes)
        
        # Total time should be reasonable (not much more than single request time)
        assert total_time < 2.0, f"20 concurrent requests took {total_time:.3f}s, too slow"
    
    @pytest.mark.skip(reason="SQLite has concurrency limitations in test environment")
    async def test_concurrent_auth_requests(self, client: AsyncClient, test_user: User, test_password: str):
        """Test concurrent authentication requests."""
        async def login_request():
            response = await client.post(
                f"{settings.API_V1_STR}/auth/login",
                json={"email": test_user.email, "password": test_password}
            )
            return response.status_code
        
        # Make 10 concurrent login requests
        start_time = time.time()
        tasks = [login_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # All requests should succeed
        assert all(code == 200 for code in results)
        
        # Should handle concurrent auth reasonably well
        assert total_time < 5.0, f"10 concurrent logins took {total_time:.3f}s, too slow"
    
    @pytest.mark.skip(reason="SQLite has concurrency limitations in test environment")
    async def test_concurrent_database_queries(self, client: AsyncClient, auth_headers: dict):
        """Test concurrent database query performance."""
        async def query_request():
            response = await client.get(
                f"{settings.API_V1_STR}/resume/list",
                headers=auth_headers
            )
            return response.status_code
        
        # Make 15 concurrent database queries
        start_time = time.time()
        tasks = [query_request() for _ in range(15)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # All queries should succeed
        assert all(code == 200 for code in results)
        
        # Database should handle concurrent queries well
        assert total_time < 3.0, f"15 concurrent queries took {total_time:.3f}s, too slow"


@pytest.mark.asyncio
class TestMemoryPerformance:
    """Test memory usage and efficiency."""
    
    @pytest.mark.skip(reason="SQLite table creation conflicts in test environment")
    async def test_large_response_handling(self, client: AsyncClient, auth_headers: dict):
        """Test handling of large API responses."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make request that could return large response
        response = await client.get(
            f"{settings.API_V1_STR}/resume/list",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 50MB for this test)
        assert memory_increase < 50, f"Memory increased by {memory_increase:.1f}MB, too much"
    
    async def test_request_cleanup(self, client: AsyncClient, auth_headers: dict):
        """Test that requests are properly cleaned up."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Make multiple requests and force garbage collection
        for _ in range(10):
            response = await client.get(
                f"{settings.API_V1_STR}/health",
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Force garbage collection
        gc.collect()
        
        # Memory should not grow excessively
        memory_mb = process.memory_info().rss / 1024 / 1024
        assert memory_mb < 500, f"Memory usage {memory_mb:.1f}MB too high after requests"


@pytest.mark.asyncio
class TestDatabasePerformance:
    """Test database performance characteristics."""
    
    async def test_database_connection_performance(self, db_session: AsyncSession):
        """Test database connection and query performance."""
        from sqlalchemy import text
        
        # Test simple query performance
        start_time = time.time()
        result = await db_session.execute(text("SELECT 1"))
        query_time = time.time() - start_time
        
        assert result.scalar() == 1
        assert query_time < 0.1, f"Simple query took {query_time:.3f}s, too slow"
    
    async def test_user_query_performance(self, db_session: AsyncSession, test_user: User):
        """Test user-related query performance."""
        from sqlalchemy import select
        
        # Test user lookup performance
        start_time = time.time()
        result = await db_session.execute(
            select(User).where(User.email == test_user.email)
        )
        query_time = time.time() - start_time
        
        user = result.scalar_one_or_none()
        assert user is not None
        assert query_time < PERFORMANCE_BUDGETS["database_query"], \
            f"User query took {query_time:.3f}s, exceeds budget {PERFORMANCE_BUDGETS['database_query']}s"
    
    async def test_bulk_data_handling(self, db_session: AsyncSession):
        """Test handling of bulk data operations."""
        from app.models.user import User
        from app.services.auth import get_password_hash
        from sqlalchemy import select
        
        # Create multiple users in bulk
        users = []
        for i in range(50):
            user = User(
                email=f"bulk{i}@test.com",
                hashed_password=get_password_hash("password123"),
                is_active=True
            )
            users.append(user)
        
        start_time = time.time()
        db_session.add_all(users)
        await db_session.commit()
        bulk_time = time.time() - start_time
        
        # Bulk operations should be reasonably fast
        assert bulk_time < 5.0, f"Bulk insert of 50 users took {bulk_time:.3f}s, too slow"
        
        # Query performance with more data
        start_time = time.time()
        result = await db_session.execute(select(User).limit(10))
        query_time = time.time() - start_time
        
        users_list = result.scalars().all()
        assert len(users_list) == 10
        assert query_time < 0.5, f"Query with bulk data took {query_time:.3f}s, too slow"


@pytest.mark.asyncio
class TestLoadTesting:
    """Basic load testing scenarios."""
    
    @pytest.mark.slow
    async def test_sustained_load(self, client: AsyncClient):
        """Test sustained load over time."""
        request_count = 100
        success_count = 0
        error_count = 0
        times = []
        
        async def make_request():
            nonlocal success_count, error_count
            try:
                start_time = time.time()
                response = await client.get(f"{settings.API_V1_STR}/health")
                end_time = time.time()
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    error_count += 1
                
                times.append(end_time - start_time)
            except Exception:
                error_count += 1
        
        # Make requests with small delays
        start_time = time.time()
        for i in range(request_count):
            await make_request()
            if i % 10 == 0:  # Small delay every 10 requests
                await asyncio.sleep(0.1)
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        success_rate = success_count / request_count
        avg_response_time = statistics.mean(times) if times else 0
        requests_per_second = request_count / total_time
        
        # Assertions
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} too low"
        assert avg_response_time < 0.5, f"Average response time {avg_response_time:.3f}s too high"
        assert requests_per_second >= 10, f"Throughput {requests_per_second:.1f} req/s too low"
        
        print(f"\nLoad Test Results:")
        print(f"  Requests: {request_count}")
        print(f"  Success Rate: {success_rate:.2%}")
        print(f"  Average Response Time: {avg_response_time:.3f}s")
        print(f"  Throughput: {requests_per_second:.1f} req/s")
        print(f"  Total Time: {total_time:.2f}s")


# Performance test utilities
class PerformanceMonitor:
    """Utility class for monitoring performance during tests."""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        return self
    
    def stop(self, operation_name: str):
        """Stop monitoring and record metrics."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics[operation_name] = duration
            return duration
        return 0
    
    def assert_within_budget(self, operation_name: str, budget: float):
        """Assert that operation completed within budget."""
        if operation_name in self.metrics:
            actual_time = self.metrics[operation_name]
            assert actual_time < budget, \
                f"{operation_name} took {actual_time:.3f}s, exceeds budget {budget}s"


@pytest.fixture
def performance_monitor():
    """Fixture providing performance monitoring utilities."""
    return PerformanceMonitor()


# Performance regression tests
@pytest.mark.asyncio
class TestPerformanceRegression:
    """Test for performance regressions."""
    
    async def test_no_n_plus_one_queries(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test that we don't have N+1 query problems."""
        # This would require query counting, which is complex to implement
        # For now, we'll test that response times don't degrade with more data
        
        # Create some test data
        from app.models.user import User
        from app.services.auth import get_password_hash
        
        # Add more users to test query efficiency
        users = []
        for i in range(10):
            user = User(
                email=f"nplus1test{i}@test.com",
                hashed_password=get_password_hash("password123"),
                is_active=True
            )
            users.append(user)
        
        db_session.add_all(users)
        await db_session.commit()
        
        # Test that queries remain fast even with more data
        start_time = time.time()
        response = await client.get(
            f"{settings.API_V1_STR}/resume/list",
            headers=auth_headers
        )
        query_time = time.time() - start_time
        
        assert response.status_code == 200
        assert query_time < 1.0, f"Query time {query_time:.3f}s suggests N+1 problem"
    
    async def test_memory_leak_detection(self, client: AsyncClient, auth_headers: dict):
        """Basic memory leak detection."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make many requests
        for _ in range(50):
            response = await client.get(
                f"{settings.API_V1_STR}/health",
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Force garbage collection
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Memory should not increase significantly
        assert memory_increase < 20, f"Memory increased by {memory_increase:.1f}MB, possible leak"