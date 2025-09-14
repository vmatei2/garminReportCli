import json
from agents.baseAgent import LLMBase, UserProfile
from typing import Dict, Any, List
from pydantic import BaseModel


class CoachFeedback(BaseModel):
    """Schema for the feedback we will receive from our AI coach """
    feedback: str
    confidence: float
    reasoning: str


class AICoach(LLMBase):
    """
    AI Powered Personal Trainer - aimed specifically for busy individuals wanting to train,
    be pushed and receive honest feedback (pros and cons) on how their training is progressing,
    depending on their goals
    """

    def prepare_prompt(self, input_data: Dict[str, Any]) -> str:
        """
        Prepare the prompt for the coach to give feedback on
        Function will take in user's Garmin data to understand their training pattenrs
        :return:
        """
        activities = input_data.get('activities', []) # default to empty list
        user_profile = input_data.get('profile', {})

        activities_str = json.dumps(activities, default=str, indent=2)
        user_profile_str = json.dumps(user_profile, default=str, indent=2)

        prompt = f"""
        Based on the following raw data, please give feedback on the User's current training structure,
        taking into account their overall fitness trend.
        
        Please consider their training ambitions, their current age and sex. Be an honest coach, telling them whether they should push harder,
        whether they are overtraining - or if there are any signs of training heading in the wrong direction. Similarly, if everything looks good,
        be positive and encouraging.
        
        The training data you are receiving is aggregated weekly. Where average_hr is the mean, duration is the sum, max_hr shows maximum, max_speed also showing maximum.
        Where you see activity type = conditioning, that represents high-intensity circuit training, with a Hyrox focus.
        
        User data:
        - Training: {activities_str}
        - User Profile: {user_profile_str}

        Your Task:
        - Analyse the given data and asses how the user is progressing relative to their physical potential, previous training and overall ambitions.
        - Adjust for user profile (age, weight, height, sex, full-time job) to ensure training is relevant and sufficient. I.e. an investment banker will have less time than a personal trainer.
        - Deliver clear, honest feedback, be it good or bad, from which the user can take something productive and guide their trainning going forward. Feedback with a clear focus on the most recent (minimum of 4 weeks) of training.
        - Give actionable advice for next week of training.
        
        Reasoning steps:
        - Evaluate endurance and HR zones from Garmin
        - Understand user profile and VO2 Max history
        - Assess overall training load in terms of time / distance covered
        - Consider risks
        - Focus on the last 4 weeks of data when giving feedback relative to user's goals.
        - Be aware of the athlete's training goals and history - but make sure there is a clear focus on the most recent perforamnce trends.
        - Deliver an honest piece of feedback.
        
        
        Return the training plan in the following JSON format exactly:
        
        {{
            "feedback": "string",
            "confidence": float between 0 and 100,
            "reasoning": "string"
        }} 
"""
        return prompt

    def generate_feedback(self, activities: List=None, profile: UserProfile=None):
        """
        Generate the feedback from the AI coach - using the user's Garmin data and profile as inputs
        :param activities:
        :param profile:
        :return:
        """
        # initialise dictionary to be filled in
        input_data = {}
        input_data['profile'] = {
            'age': profile.age,
            'height': profile.height,
            'weight': profile.weight,
            'sex': profile.sex,
            'ambitions': profile.ambitions,
            'current_job': profile.current_job
        }

        if not activities.empty:
            input_data['activities'] = activities.to_dict(orient='records')
        prompt = self.prepare_prompt(input_data)

        # Actual LLM call
        return self.call_llm(
            input_data=prompt,
            system_message="You are an expert coach with years of experience. You have coached both busy professionals and high-performance athletes."
                           "You know exactly what it takes to deliver a high performance program, and are able to spot trends before it' too late."
                           "You can provide both positive and negqtive feedback and are not afraid to hurt someone's feelings. Always take into account their ambitions and current and past fitness levels.",
            pydantic_model=CoachFeedback,
            agent_name="AI Fitness Coach"
        )

