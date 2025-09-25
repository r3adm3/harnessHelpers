#!/usr/bin/env python3
"""
Harness API Pipeline AppID Tag Counter Script

This script connects to the Harness API to enumerate all pipelines across
organizations and projects, then counts how many pipelines are tagged with
a specific appID in their YAML representation.

Requirements:
- requests library: pip install requests
- pyyaml library: pip install pyyaml
- Valid Harness API token with appropriate permissions
- Account ID from your Harness instance
- HARNESS_API_TOKEN and HARNESS_ACCT_ID environment variables set

Usage:
    export HARNESS_API_TOKEN="your_token_here"
    export HARNESS_ACCT_ID="your_account_id_here"
    python pipelineAppIdTagCounter.py
"""

import requests
import json
import os
import yaml
import re
from typing import Dict, List, Optional, Set, Tuple
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
            if hasattr(e, 'response') and e.response is not None and e.response.status_code != 404:
                print(f"      ⚠️  API request failed: {e}")
                print(f"      Response status: {e.response.status_code}")
            return None
    
    def get_organizations(self) -> List[Dict]:
        """Get all organizations in the account"""
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
            
            if page_data.get('last', True):
                break
            
            page += 1
        
        return organizations
    
    def get_projects_in_org(self, org_identifier: str) -> List[Dict]:
        """Get all projects in an organization"""
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
            
            if page_data.get('last', True):
                break
            
            page += 1
        
        return projects
    
    def get_pipelines_in_project(self, org_identifier: str, project_identifier: str) -> List[Dict]:
        """Get all pipelines in a project"""
        # Try different API approaches for getting pipelines
        approaches = [
            {
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
                "method": "GET", 
                "endpoint": "/pipelines",
                "params": {
                    'accountIdentifier': self.account_id,
                    'orgIdentifier': org_identifier,
                    'projectIdentifier': project_identifier,
                    'page': 0,
                    'limit': 100
                }
            }
        ]
        
        for approach in approaches:
            try:
                response = self._make_request(
                    method=approach['method'],
                    endpoint=approach['endpoint'],
                    params=approach['params'],
                    data=approach.get('data')
                )
                
                if response:
                    data = response.get('data', response)
                    
                    if isinstance(data, list):
                        return data
                    elif data.get('content'):
                        return data['content']
                    elif data.get('pipelines'):
                        return data['pipelines']
                        
            except Exception:
                continue
        
        return []
    
    def get_pipeline_yaml(self, org_identifier: str, project_identifier: str, pipeline_identifier: str) -> Optional[str]:
        """
        Get the YAML representation of a specific pipeline
        
        Args:
            org_identifier: Organization identifier
            project_identifier: Project identifier
            pipeline_identifier: Pipeline identifier
            
        Returns:
            Pipeline YAML as string or None if error
        """
        # Try different endpoints for getting pipeline YAML
        endpoints = [
            f"/pipelines/{pipeline_identifier}",
            f"/pipeline/api/pipelines/{pipeline_identifier}"
        ]
        
        params = {
            'accountIdentifier': self.account_id,
            'orgIdentifier': org_identifier,
            'projectIdentifier': project_identifier
        }
        
        for endpoint in endpoints:
            response = self._make_request('GET', endpoint, params=params)
            
            if response:
                data = response.get('data', response)
                
                # Check for YAML in different response structures
                if isinstance(data, dict):
                    # Look for yaml field
                    if 'yamlPipeline' in data:
                        return data['yamlPipeline']
                    elif 'yaml' in data:
                        return data['yaml']
                    elif 'pipelineYaml' in data:
                        return data['pipelineYaml']
                    # If we have pipeline data, try to convert to YAML
                    elif 'pipeline' in data:
                        try:
                            return yaml.dump(data['pipeline'], default_flow_style=False)
                        except:
                            pass
                    # Try to convert entire data to YAML
                    else:
                        try:
                            return yaml.dump(data, default_flow_style=False)
                        except:
                            pass
        
        return None

def extract_app_ids_from_yaml(yaml_content: str) -> Set[str]:
    """
    Extract appID values from pipeline YAML content
    
    Args:
        yaml_content: Pipeline YAML as string
        
    Returns:
        Set of appID values found in the YAML
    """
    app_ids = set()
    
    try:
        # Parse YAML
        yaml_data = yaml.safe_load(yaml_content)
        
        # Convert to string for regex searching (handles nested structures)
        yaml_str = yaml.dump(yaml_data) if yaml_data else yaml_content
        
        # Search for appID patterns (case insensitive)
        patterns = [
            r'appid:\s*["\']?([^"\'\s\n]+)["\']?',  # appid: value
            r'app_id:\s*["\']?([^"\'\s\n]+)["\']?', # app_id: value
            r'appId:\s*["\']?([^"\'\s\n]+)["\']?',  # appId: value (camelCase)
            r'application_id:\s*["\']?([^"\'\s\n]+)["\']?', # application_id: value
            r'applicationId:\s*["\']?([^"\'\s\n]+)["\']?'   # applicationId: value
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, yaml_str, re.IGNORECASE)
            app_ids.update(matches)
        
        # Also search in tags section
        if isinstance(yaml_data, dict):
            tags = yaml_data.get('tags', {})
            if isinstance(tags, dict):
                for key, value in tags.items():
                    if 'appid' in key.lower() or 'app_id' in key.lower():
                        app_ids.add(str(value))
    
    except yaml.YAMLError:
        # If YAML parsing fails, fall back to regex on raw content
        patterns = [
            r'appid:\s*["\']?([^"\'\s\n]+)["\']?',
            r'app_id:\s*["\']?([^"\'\s\n]+)["\']?',
            r'appId:\s*["\']?([^"\'\s\n]+)["\']?',
            r'application_id:\s*["\']?([^"\'\s\n]+)["\']?',
            r'applicationId:\s*["\']?([^"\'\s\n]+)["\']?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, yaml_content, re.IGNORECASE)
            app_ids.update(matches)
    
    return app_ids

def main():
    """Main function to count pipelines by appID"""
    
    # Configuration
    API_TOKEN = os.getenv('HARNESS_API_TOKEN')
    ACCOUNT_ID = os.getenv('HARNESS_ACCT_ID')
    BASE_URL = "https://app.harness.io"
    
    # Validate configuration
    if not API_TOKEN:
        print("❌ HARNESS_API_TOKEN environment variable is not set.")
        print("\nTo set your API token:")
        print("  export HARNESS_API_TOKEN='your_harness_api_token_here'")
        sys.exit(1)
    
    if not ACCOUNT_ID:
        print("❌ HARNESS_ACCT_ID environment variable is not set.")
        print("\nTo set your account ID:")
        print("  export HARNESS_ACCT_ID='your_harness_account_id_here'")
        sys.exit(1)
    
    # Initialize client
    client = HarnessAPIClient(API_TOKEN, ACCOUNT_ID, BASE_URL)
    
    print("🚀 Starting pipeline appID analysis...")
    print(f"📊 Account ID: {ACCOUNT_ID}")
    print("=" * 70)
    
    # Get all organizations
    print("📂 Fetching organizations...")
    organizations = client.get_organizations()
    
    if not organizations:
        print("❌ No organizations found or API call failed.")
        sys.exit(1)
    
    print(f"✅ Found {len(organizations)} organizations")
    
    # Track results
    app_id_counts = defaultdict(int)
    pipeline_details = defaultdict(list)  # appID -> list of (org, project, pipeline) tuples
    total_pipelines = 0
    processed_pipelines = 0
    pipelines_with_app_ids = 0
    
    # Process each organization
    for org in organizations:
        org_data = org.get('organization', org)
        org_id = org_data.get('identifier', 'unknown')
        org_name = org_data.get('name', org_id)
        
        print(f"\n📁 Processing organization: {org_name} ({org_id})")
        
        # Get projects in this organization
        projects = client.get_projects_in_org(org_id)
        print(f"   📋 Found {len(projects)} projects")
        
        for project in projects:
            project_data = project.get('project', project)
            project_id = project_data.get('identifier', 'unknown')
            project_name = project_data.get('name', project_id)
            
            if project_id == 'unknown':
                continue
            
            print(f"      🔧 Processing project: {project_name}")
            
            # Get pipelines in this project
            pipelines = client.get_pipelines_in_project(org_id, project_id)
            total_pipelines += len(pipelines)
            
            for pipeline in pipelines:
                pipeline_data = pipeline.get('pipeline', pipeline)
                pipeline_id = pipeline_data.get('identifier', pipeline_data.get('name', 'unknown'))
                pipeline_name = pipeline_data.get('name', pipeline_id)
                
                if pipeline_id == 'unknown':
                    continue
                
                # Get pipeline YAML
                yaml_content = client.get_pipeline_yaml(org_id, project_id, pipeline_id)
                processed_pipelines += 1
                
                if yaml_content:
                    # Extract appIDs from YAML
                    app_ids = extract_app_ids_from_yaml(yaml_content)
                    
                    if app_ids:
                        pipelines_with_app_ids += 1
                        print(f"         📌 {pipeline_name}: {', '.join(sorted(app_ids))}")
                        
                        for app_id in app_ids:
                            app_id_counts[app_id] += 1
                            pipeline_details[app_id].append((org_name, project_name, pipeline_name))
                    else:
                        print(f"         ⚪ {pipeline_name}: No appID found")
                else:
                    print(f"         ❌ {pipeline_name}: Failed to get YAML")
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 PIPELINE APPID ANALYSIS RESULTS")
    print("=" * 70)
    
    if app_id_counts:
        print("🏷️  APPID USAGE SUMMARY:")
        print("-" * 50)
        for app_id, count in sorted(app_id_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_pipelines * 100) if total_pipelines > 0 else 0
            print(f"{app_id:<30} | {count:>3} pipelines ({percentage:>5.1f}%)")
        
        print("\n📋 DETAILED BREAKDOWN:")
        print("-" * 50)
        for app_id in sorted(app_id_counts.keys()):
            print(f"\n🏷️  AppID: {app_id} ({app_id_counts[app_id]} pipelines)")
            for org_name, project_name, pipeline_name in sorted(pipeline_details[app_id]):
                print(f"    📁 {org_name} → 📋 {project_name} → 🔧 {pipeline_name}")
    else:
        print("❌ No appIDs found in any pipeline YAML")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("📈 SUMMARY STATISTICS")
    print("=" * 70)
    print(f"📊 Total pipelines found: {total_pipelines}")
    print(f"🔍 Pipelines processed: {processed_pipelines}")
    print(f"🏷️  Pipelines with appIDs: {pipelines_with_app_ids}")
    print(f"🆔 Unique appIDs found: {len(app_id_counts)}")
    
    if total_pipelines > 0:
        coverage = (pipelines_with_app_ids / total_pipelines * 100)
        print(f"📊 AppID coverage: {coverage:.1f}%")
    
    if app_id_counts:
        most_used = max(app_id_counts.items(), key=lambda x: x[1])
        print(f"🏆 Most used appID: {most_used[0]} ({most_used[1]} pipelines)")

if __name__ == "__main__":
    main()