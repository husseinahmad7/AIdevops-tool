# use .env in github ci
```
...
      - name: Create environment file
        working-directory: ${{ matrix.service }}
        run: |
          # Create .env file from GitHub Secrets
          cat > .env << EOF
          API_KEY=${{ secrets.API_KEY }}
          DATABASE_URL=${{ secrets.DATABASE_URL }}
          # Add other environment variables as needed
          EOF
        env:
          API_KEY: ${{ secrets.API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
...
```

# use .env in gitlab ci

```
pytest:
  stage: test
  script:
    - |
      for svc in api-gateway user-management infrastructure-monitor ai-prediction log-analysis cicd-optimization resource-optimization natural-language notification reporting; do
        echo "===> Testing $svc"
        cd "$svc"

        # Create .env file from GitLab CI variables
        cat > .env << EOF
        API_KEY=${API_KEY}
        DATABASE_URL=${DATABASE_URL}
        # Add other environment variables as needed
        EOF
        ...
```
