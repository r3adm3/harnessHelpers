#!/usr/bin/env python3
"""
Harness API Pipeline Counter Script

This script connects to the Harness API to count the number of pipelines
per organization in your Harness account.

Requirements:
- requests library: pip install requests
- Valid Harness API token with appropriate permissions
- Account ID from your Harness instance
- HARNESS_API_TOKEN environment variable set

Usage:
    export HARNESS_API_TOKEN="your_token_here"
    python harness_pipeline_counter.py
"""

import requests
import json
import os
from typing import Dict, List, Optional
from collections import defaultdict
import sys

class HarnessAPIClient:
    """Client for interacting with Harness API"""
    
    def __init__(self, api_token: str, account_id: str, base_url: str = "https://app.harness.io"):
        """
        Initialize Harness API client
        
        Args:
            api_token: Harness API token (Personal Access Token or Service Account token)
            account_id: Your Harness account ID
            base_url: Harness instance base URL (default: https://app.harness.io)
        """
        self.api_token = api_token
        self.account_id = account_id
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Set up authentication headers
        self.session.headers.update({
            'x-api-key': self.api_token,
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """
        Make HTTP request to Harness API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            
        Returns:
            JSON response data or None if error
        """
        # Handle different API path prefixes
        if endpoint.startswith('/pipeline/api/'):
            url = f"{self.base_url}{endpoint}"  # pipeline APIs don't use /ng prefix
        else:
            url = f"{self.base_url}/ng/api{endpoint}"  # NextGen APIs use /ng/api prefix
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"      ⚠️  API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"      Response status: {e.response.status_code}")
                if e.response.status_code != 404:  # Don't show response text for 404s to reduce noise
                    print(f"      Response text: {e.response.text}")
            return None
    
    def get_organizations(self) -> List[Dict]:
        """
        Get all organizations in the account
        
        Returns:
            List of organization dictionaries
        """
        endpoint = f"/organizations"
        params = {
            'accountIdentifier': self.account_id,
            'pageIndex': 0,
            'pageSize': 100
        }
        
        organizations = []
        page = 0
        
        while True:
            params['pageIndex'] = page
            response = self._make_request('GET', endpoint, params=params)
            
            if not response or not response.get('data'):
                break
            
            page_data = response['data']
            if not page_data.get('content'):
                break
                
            organizations.extend(page_data['content'])
            
            # Check if there are more pages
            if page_data.get('last', True):
                break
            
            page += 1
        
        return organizations
    
    def get_projects_in_org(self, org_identifier: str) -> List[Dict]:
        """
        Get all projects in an organization
        
        Args:
            org_identifier: Organization identifier
            
        Returns:
            List of project dictionaries
        """
        endpoint = f"/projects"
        params = {
            'accountIdentifier': self.account_id,
            'orgIdentifier': org_identifier,
            'pageIndex': 0,
            'pageSize': 100
        }
        
        projects = []
        page = 0
        
        while True:
            params['pageIndex'] = page
            response = self._make_request('GET', endpoint, params=params)
            
            if not response or not response.get('data'):
                break
            
            page_data = response['data']
            if not page_data.get('content'):
                break
                
            projects.extend(page_data['content'])
            
            # Check if there are more pages
            if page_data.get('last', True):
                break
            
            page += 1
        
        return projects
    
    def get_pipelines_in_project(self, org_identifier: str, project_identifier: str) -> List[Dict]:
        """
        Get all pipelines in a project
        
        Args:
            org_identifier: Organization identifier
            project_identifier: Project identifier
            
        Returns:
            List of pipeline dictionaries
        """
        # Try different API approaches for getting pipelines
        approaches = [
            {
                "name": "POST /pipeline/api/pipelines/list",
                "method": "POST",
                "endpoint": "/pipeline/api/pipelines/list",
                "data": {
                    "filterType": "PipelineSetup"
                },
                "params": {
                    'accountIdentifier': self.account_id,
                    'orgIdentifier': org_identifier,
                    'projectIdentifier': project_identifier,
                    'page': 0,
                    'size': 100
                }
            },
            {
                "name": "GET /pipelines with query params",
                "method": "GET", 
                "endpoint": "/pipelines",
                "params": {
                    'accountIdentifier': self.account_id,
                    'orgIdentifier': org_identifier,
                    'projectIdentifier': project_identifier,
                    'page': 0,
                    'limit': 100
                }
            },
            {
                "name": "POST /ng/api/pipelines/list",
                "method": "POST",
                "endpoint": "/pipelines/list",
                "data": {
                    "filterType": "PipelineSetup"
                },
                "params": {
                    'accountIdentifier': self.account_id,
                    'orgIdentifier': org_identifier,
                    'projectIdentifier': project_identifier
                }
            }
        ]
        
        for approach in approaches:
            #print(f"      🔍 Trying: {approach['name']}")
            
            try:
                response = self._make_request(
                    method=approach['method'],
                    endpoint=approach['endpoint'],
                    params=approach['params'],
                    data=approach.get('data')
                )
                
                if response:
                    # Check different response structures
                    data = response.get('data', response)
                    
                    if isinstance(data, list):
                        print(f"      ✅ Success! Found {len(data)} pipelines")
                        return data
                    elif data.get('content'):
                        pipelines = data['content']
                        print(f"      ✅ Success! Found {len(pipelines)} pipelines")
                        return pipelines
                    elif data.get('pipelines'):
                        pipelines = data['pipelines']
                        print(f"      ✅ Success! Found {len(pipelines)} pipelines")
                        return pipelines
                    elif 'totalElements' in data:
                        print(f"      ✅ Success! Found {data.get('totalElements', 0)} total pipelines")
                        return data.get('content', [])
                    else:
                        print(f"      ❓ Unexpected response structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                        
            except Exception as e:
                print(f"      ❌ Failed: {str(e)}")
                continue
        
        print(f"      ❌ All approaches failed for project {project_identifier}")
        return []

def main():
    """Main function to count pipelines per organization"""
    
    # Configuration - UPDATE THESE VALUES
    API_TOKEN = os.getenv('HARNESS_API_TOKEN')
    ACCOUNT_ID = os.getenv('HARNESS_ACCT_ID')
    BASE_URL = "https://app.harness.io"  # Change if using different Harness instance
    
    # Validate configuration
    if not API_TOKEN:
        print("❌ HARNESS_API_TOKEN environment variable is not set.")
        print("\nTo set your API token:")
        print("  export HARNESS_API_TOKEN='your_harness_api_token_here'")
        print("\nTo get your API token:")
        print("1. Go to Harness UI > Account Settings > Access Control > API Keys")
        print("2. Create a new Personal Access Token or Service Account token")
        sys.exit(1)
    
    if ACCOUNT_ID == "your_account_id_here":
        print("❌ Please update the ACCOUNT_ID in the script before running.")
        print("\nTo get your Account ID:")
        print("1. Look in the URL when logged into Harness")
        print("2. Or check Account Settings in the Harness UI")
        sys.exit(1)
    
    # Initialize client
    client = HarnessAPIClient(API_TOKEN, ACCOUNT_ID, BASE_URL)
    
    print("🚀 Starting pipeline count analysis...")
    print(f"📊 Account ID: {ACCOUNT_ID}")
    print("=" * 50)
    
    # Get all organizations
    print("📂 Fetching organizations...")
    organizations = client.get_organizations()
    
    if not organizations:
        print("❌ No organizations found or API call failed.")
        sys.exit(1)
    
    print(f"✅ Found {len(organizations)} organizations")
    
    # Count pipelines per organization
    pipeline_counts = defaultdict(int)
    org_details = {}
    total_pipelines = 0
    
    for org in organizations:
        # Handle nested organization structure
        org_data = org.get('organization', org)  # Use 'organization' key if it exists, otherwise use org directly
        org_id = org_data.get('identifier', 'unknown')
        org_name = org_data.get('name', org_id)
        org_details[org_id] = org_name
        
        print(f"\n📁 Processing organization: {org_name} ({org_id})")
        
        # Get projects in this organization
        projects = client.get_projects_in_org(org_id)
        print(f"   📋 Found {len(projects)} projects")
        
        org_pipeline_count = 0
        
        for project in projects:
            # Handle nested project structure
            project_data = project.get('project', project)  # Use 'project' key if it exists, otherwise use project directly
            project_id = project_data.get('identifier', 'unknown')
            project_name = project_data.get('name', project_id)
            
            # Skip if we still don't have a valid project_id
            if project_id == 'unknown':
                print(f"      ⚠️  Skipping project with unknown identifier: {project}")
                continue
            
            # Get pipelines in this project
            pipelines = client.get_pipelines_in_project(org_id, project_id)
            project_pipeline_count = len(pipelines)
            org_pipeline_count += project_pipeline_count
            
            if project_pipeline_count > 0:
                print(f"      🔧 {project_name}: {project_pipeline_count} pipelines")
        
        pipeline_counts[org_id] = org_pipeline_count
        total_pipelines += org_pipeline_count
        print(f"   📊 Organization total: {org_pipeline_count} pipelines")
    
    # Display results
    print("\n" + "=" * 50)
    print("📊 PIPELINE COUNT SUMMARY")
    print("=" * 50)
    
    for org_id, count in sorted(pipeline_counts.items(), key=lambda x: x[1], reverse=True):
        org_name = org_details.get(org_id, org_id)
        percentage = (count / total_pipelines * 100) if total_pipelines > 0 else 0
        print(f"{org_name:<30} | {count:>5} pipelines ({percentage:>5.1f}%)")
    
    print("-" * 50)
    print(f"{'TOTAL':<30} | {total_pipelines:>5} pipelines")
    print("=" * 50)
    
    # Additional statistics
    if organizations:
        avg_pipelines = total_pipelines / len(organizations)
        print(f"\n📈 Average pipelines per organization: {avg_pipelines:.1f}")
        
        max_org = max(pipeline_counts.items(), key=lambda x: x[1]) if pipeline_counts else None
        if max_org:
            max_org_name = org_details.get(max_org[0], max_org[0])
            print(f"🏆 Organization with most pipelines: {max_org_name} ({max_org[1]} pipelines)")

if __name__ == "__main__":
    main()