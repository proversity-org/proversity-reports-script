

settings = {
    "API_RESULT": {
        "status": "SUCCESS",
        "result": {
            "course-v1:edx+cs108+2019": [
                {
                    "username": "verified",
                    "cohort": "Default Group",
                    "user_id": 8,
                    "time_between_sessions": 45,
                    "average_session_length": 55,
                    "team": "team11",
                    "cumulative_grade": 0.3,
                    "timeliness_of_submissions": -2,
                    "number_of_graded_assessment": 5,
                    "weekly_clicks": 0,
                    "has_verified_certificate": False,
                    "email": "verified@example.com"
                },
                {
                    "username": "audit",
                    "cohort": "Cohort1",
                    "user_id": 7,
                    "time_between_sessions": 25,
                    "average_session_length": 0,
                    "team": "",
                    "cumulative_grade": 0.7,
                    "timeliness_of_submissions": 0.3,
                    "number_of_assessment_submissions": 28,
                    "weekly_clicks": 0,
                    "has_verified_certificate": False,
                    "email": "audit@example.com"
                }
            ],
            "course-v1:edx+cs195+2018": [
                {
                    "username": "honor",
                    "cohort": "Default Group",
                    "user_id": 8,
                    "time_between_sessions": 89,
                    "average_session_length": 0,
                    "team": "team11",
                    "cumulative_grade": 0.3,
                    "timeliness_of_submissions": 0.3,
                    "number_of_assessment_submissions": 28,
                    "weekly_clicks": 0,
                    "has_verified_certificate": False,
                    "email": "verified@example.com"
                },
                {
                    "username": "audit",
                    "cohort": "Cohort1",
                    "user_id": 7,
                    "time_between_sessions": 15,
                    "average_session_length": 0,
                    "team": "",
                    "cumulative_grade": 0.87,
                    "timeliness_of_submissions": 0.3,
                    "number_of_assessment_submissions": 28,
                    "weekly_clicks": 0,
                    "has_verified_certificate": False,
                    "email": "audit@example.com"
                }
            ],
        }
    },
    "REPORT_CONFIG": [
        {
            "metric" : "cumulative_grade",
            "passing_score": 0.8,
            "graph_title": "Cumulative Grade",
            "ylabel": "%",
        },
        {
            "metric" : "timeliness_of_submissions",
            "passing_score": 3,
            "graph_title": "Timeliness",
            "ylabel": "Avg Days Before Deadline",
        },
        {
            "metric" : "average_session_length",
            "passing_score": 84,
            "graph_title": "Avg Session Length",
            "ylabel": "Minutes",
        },
        {
            "metric" : "number_of_graded_assessment",
            "passing_score": 21,
            "graph_title": "Submissions",
            "ylabel": "Count",
        },
        {
            "metric" : "time_between_sessions",
            "passing_score": 65,
            "graph_title": "Time Btwn Sessions",
            "ylabel": "Hours",
        }
    ],
    "SENGRID_CONF": {
        "API_KEY": "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",
        "SENDER": {"email": "pearsonx3@example.com", "name": "PearsonX3"},
        "RECEIVER": {"email": "diego.millan@edunext.co"},
        "IMAGE_CID": "r4nd0mc0nt3nt",
        "TEMPATE_ID": "d-7144fea70bdd4c48b04af931357cdf42",

    }
}


# ##########################################################################################

def test_pipeline_and_deliver():
    # get data
    # generate subplots from data
    # generate graph
    # get graph
    # build message
    # send message

    from proversity_reports_script.messages.helpers import (
        generate_student_subplots,
        generate_graph,
        get_graph,
    )
    from proversity_reports_script.messages.sendgrid import (
        SendGridSender,
    )

    sendgrid_conf = settings["SENGRID_CONF"]
    data = settings["API_RESULT"]["result"]
    # passing data from API
    subplots_for_student = generate_student_subplots(data["course-v1:edx+cs108+2019"][0], settings["REPORT_CONFIG"])
    # import ipdb; ipdb.set_trace()    
    graph_generated = generate_graph(subplots=subplots_for_student)
    image_string = None

    if graph_generated:
        image_string = get_graph()

    if not image_string:
        print ("no hay imagen -- no se envia mensaje")
        return None

    sender = SendGridSender(sendgrid_conf["API_KEY"])
    if not sender.api_client:
        print ("no hay cliente sendgrid -- no se envia mensaje")
        return None


    receiver = {"email": "diego.millan@edunext.co"}
    dindata = {'name': 'Rafael Martinez', 'subject': "Week {}: {} Learning Tracker".format(1, "course-v1:edx+cs108+2019")}
    message_data = {
        "image_string": image_string,
        "sender": sendgrid_conf["SENDER"],
        "receiver" : receiver,
        "dynamic_template_data": dindata,
        "template_id": sendgrid_conf["TEMPATE_ID"],
        "graph_cid": sendgrid_conf["IMAGE_CID"],
    }
    message = sender.build_message(**message_data)
    sender.send_message(message)
    
    return "Pipeline ejecutado completo"
