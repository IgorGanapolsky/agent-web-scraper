-- DAILY_REVENUE

                SELECT 
                    DATE(transaction_timestamp) as date,
                    SUM(amount) as daily_revenue,
                    COUNT(DISTINCT user_id) as paying_customers,
                    AVG(amount) as avg_transaction_value
                FROM `cfo-bi-dashboard.revenue_analytics.revenue`
                WHERE DATE(transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                GROUP BY DATE(transaction_timestamp)
                ORDER BY date DESC
            

-- CONVERSION_FUNNEL

                WITH funnel_data AS (
                    SELECT 
                        user_id,
                        MIN(CASE WHEN event_name = 'trial_signup' THEN event_timestamp END) as trial_signup_time,
                        MIN(CASE WHEN event_name = 'diagnostic_session_booked' THEN event_timestamp END) as diagnostic_time,
                        MIN(CASE WHEN event_name = 'pilot_customer_converted' THEN event_timestamp END) as conversion_time
                    FROM `cfo-bi-dashboard.revenue_analytics.events`
                    WHERE event_name IN ('trial_signup', 'diagnostic_session_booked', 'pilot_customer_converted')
                    AND DATE(event_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                    GROUP BY user_id
                )
                SELECT 
                    COUNT(*) as trial_signups,
                    COUNT(diagnostic_time) as diagnostic_sessions,
                    COUNT(conversion_time) as pilot_conversions,
                    ROUND(COUNT(diagnostic_time) / COUNT(*) * 100, 2) as signup_to_diagnostic_rate,
                    ROUND(COUNT(conversion_time) / COUNT(diagnostic_time) * 100, 2) as diagnostic_to_conversion_rate,
                    ROUND(COUNT(conversion_time) / COUNT(*) * 100, 2) as overall_conversion_rate
                FROM funnel_data
            

-- REVENUE_BY_TIER

                SELECT 
                    tier,
                    COUNT(DISTINCT user_id) as customer_count,
                    SUM(amount) as total_revenue,
                    AVG(amount) as avg_revenue_per_customer,
                    SUM(amount) / (SELECT SUM(amount) FROM `cfo-bi-dashboard.revenue_analytics.revenue` 
                                  WHERE DATE(transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)) * 100 as revenue_percentage
                FROM `cfo-bi-dashboard.revenue_analytics.revenue`
                WHERE DATE(transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY tier
                ORDER BY total_revenue DESC
            

