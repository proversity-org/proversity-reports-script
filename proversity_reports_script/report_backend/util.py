"""
Module containing common functions.
"""

def get_required_activity_dict(user_data):
    """
    Create a dict with the required activity data.

    Args:
        user_data: Report json data per course.
    Returns:
        Dict containing activities info.
        {
            'Multiple Choice': 'completed',
            'Image Explorer': 'completed',
            'Video': 'not_completed'
        }
    """
    required_activities_data = {}
    total_activities = user_data.get('total_activities', 0)

    if total_activities:
        total = int(total_activities)
        # Create as many 'required_activity_' as the total number of activities.
        for activity_number in range(1, total + 1): # Plus 1, because the stop argument it's not inclusive.
            required_activity_number = user_data.get('required_activity_{}'.format(activity_number), '')
            required_activity_name = user_data.get('required_activity_{}_name'.format(activity_number), '')

            # Let's add the activity number at the end of the name if two or more activities have the same name.
            if required_activity_name in required_activities_data.keys():
                required_activity_name = '{}-{}'.format(required_activity_name, activity_number)

            required_activities_data.update({
                required_activity_name: required_activity_number,
            })

    return required_activities_data
