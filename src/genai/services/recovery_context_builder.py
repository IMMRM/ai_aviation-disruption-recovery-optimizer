class RecoveryContextBuilder:

    @staticmethod
    def build(
        enriched_results_df
    ):

        context = []

        # Build summary of all assignments
        summary_lines = [
            "RECOVERY PLAN SUMMARY",
            "=" * 40
        ]

        for _, row in enriched_results_df.iterrows():

            flight = row.get('Flight', 'N/A')
            recovery_ac = row.get(
                'Recovery Aircraft', 
                'N/A'
            )

            summary_lines.append(
                f"{flight} → {recovery_ac}"
            )

        context.append(
            "\n".join(summary_lines)
        )

        context.append(
            "\nKEY CONSTRAINT:\n"
            "✓ Each flight assigned to ONE aircraft\n"
            "✓ Each aircraft used at most ONCE\n"
            "✓ Solution optimizes total recovery cost"
        )

        context.append("\n" + "=" * 40 + "\n")

        # Add detailed decision for each assignment
        for _, row in enriched_results_df.iterrows():

            # Extract values safely
            flight = row.get('Flight', 'N/A')
            failed_ac = row.get('Failed Aircraft', 'N/A')
            recovery_ac = row.get(
                'Recovery Aircraft', 
                'N/A'
            )
            recovery_cost = row.get(
                'Recovery Cost', 
                'N/A'
            )
            proximity = row.get(
                'Proximity Score', 
                'N/A'
            )
            estimated_delay = row.get(
                'Estimated Delay', 
                'N/A'
            )
            sla_impact = row.get(
                'SLA Impact', 
                'N/A'
            )
            disruption_type = row.get(
                'Disruption Type', 
                'N/A'
            )
            severity = row.get(
                'Severity', 
                'N/A'
            )
            passengers = row.get(
                'Passenger Count', 
                'N/A'
            )
            departure = row.get(
                'Departure Airport', 
                'N/A'
            )
            arrival = row.get(
                'Arrival Airport', 
                'N/A'
            )

            # Helper to safely format numeric values
            def format_number(value):
                if value == 'N/A':
                    return 'N/A'
                try:
                    # Remove $ and , if already formatted
                    if isinstance(value, str):
                        clean_val = value.replace('$', '').replace(',', '')
                        return int(float(clean_val))
                    return int(float(value))
                except (ValueError, TypeError):
                    return 'N/A'

            # Format reposition time
            reposition_text = (
                f"{format_number(estimated_delay)} minutes"
                if estimated_delay != 'N/A'
                else 'N/A'
            )

            # Format costs
            cost_val = format_number(recovery_cost)
            cost_text = (
                f"${cost_val:,}"
                if cost_val != 'N/A'
                else 'N/A'
            )

            sla_val = format_number(sla_impact)
            sla_text = (
                f"${sla_val:,}"
                if sla_val != 'N/A'
                else 'N/A'
            )

            context_entry = f"""
ASSIGNMENT: {flight} → {recovery_ac}

SELECTION RATIONALE:
• Proximity: {proximity} (lower = closer)
• Reposition: {reposition_text}
• Cost: {cost_text}
• SLA Impact: {sla_text}

DISRUPTION: {disruption_type} ({severity})
• Passengers: {passengers}
• Route: {departure} → {arrival}
• Failed Aircraft: {failed_ac}

OPTIMIZATION CONSTRAINT:
Only ONE aircraft can be assigned per flight.
{recovery_ac} was selected because it's the 
optimal solution minimizing total cost while
maintaining service level agreements.

WHY OTHER AIRCRAFT WEREN'T SELECTED:
Aircraft can be infeasible due to:
• Unavailable or in maintenance
• Insufficient passenger capacity
• Cannot reposition in time
• Higher total recovery cost
• Conflict with another assigned flight
            """

            context.append(context_entry)

        return "\n".join(context)