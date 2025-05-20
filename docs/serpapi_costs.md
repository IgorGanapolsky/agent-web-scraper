# SerpAPI Cost Estimation and Tracking

## Cost Estimation

SerpAPI charges based on the number of API calls made. Here's how to estimate costs:

### Pricing Tiers
- **Free Tier**: 100 searches/month
- **Pay-As-You-Go**: $50 for 5,000 searches ($0.01 per search)
- **Business Plans**: Custom pricing for higher volumes

### Cost Calculation
```
Total Cost = (Number of Searches × Cost per Search) + Any Additional Fees
```

### Example
- 1,000 searches at $0.01/search = $10.00
- 5,000 searches at $0.01/search = $50.00

## Cost Tracking Implementation

We've implemented a cost tracking system that:

1. **Tracks API Usage**: Each API call is logged with timestamp and cost
2. **Monthly Aggregation**: Costs are aggregated by calendar month
3. **Dashboard Display**: Shows current month's usage and estimated cost

### Usage in Code
```python
# Track API usage
from datetime import datetime
import os

def track_api_usage(cost: float):
    """Track API usage and cost."""
    month = datetime.now().strftime('%Y-%m')
    usage_file = f'api_usage_{month}.json'
    
    # Load existing data
    if os.path.exists(usage_file):
        with open(usage_file, 'r') as f:
            data = json.load(f)
    else:
        data = {
            'month': month,
            'total_searches': 0,
            'total_cost': 0.0,
            'searches': []
        }
    
    # Update data
    search_data = {
        'timestamp': datetime.now().isoformat(),
        'cost': cost
    }
    data['searches'].append(search_data)
    data['total_searches'] += 1
    data['total_cost'] = round(data['total_cost'] + cost, 2)
    
    # Save updated data
    with open(usage_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return data['total_cost']
```

## Viewing Costs

### Command Line
```bash
python -m app.cli costs
```

### Dashboard
A minimal banner is displayed in the web interface showing:
- Current month's API usage
- Estimated cost to date
- Projected monthly cost

## Best Practices
1. **Monitor Usage**: Check your dashboard regularly
2. **Set Alerts**: Configure alerts for cost thresholds
3. **Optimize Queries**: Use specific search terms to reduce unnecessary API calls
4. **Cache Results**: Implement caching for repeated queries

## Support
For any questions about billing or API usage, contact support@serpapi.com
