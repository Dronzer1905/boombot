from enum import Enum

class Status(Enum):
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3

class Node:

    def __init__(self, name):
        self.name = name

    def tick(self, context):
        raise NotImplementedError

class Condition(Node):

    def __init__(self, name, condition_function):
        super().__init__(name)
        self.condition_function = condition_function

    def tick(self, context):

        result = self.condition_function(context)

        print(
            f"  [CONDITION] {self.name} -> "
            f"{'TRUE' if result else 'FALSE'}"
        )

        if result:
            return Status.SUCCESS

        return Status.FAILURE

class Action(Node):

    def __init__(self, name, action_name):
        super().__init__(name)
        self.action_name = action_name

    def tick(self, context):

        print(f"  [ACTION] {self.name}")
        print(f"           Output -> {self.action_name}")

        context["selected_action"] = self.action_name

        return Status.SUCCESS

class Sequence(Node):

    def __init__(self, name, children):
        super().__init__(name)
        self.children = children

    def tick(self, context):

        print(f"\n[SEQUENCE] {self.name}")

        for child in self.children:

            result = child.tick(context)

            if result == Status.FAILURE:
                return Status.FAILURE

            if result == Status.RUNNING:
                return Status.RUNNING

        return Status.SUCCESS

class Selector(Node):

    def __init__(self, name, children):
        super().__init__(name)
        self.children = children

    def tick(self, context):

        print(f"\n[SELECTOR] {self.name}")

        for child in self.children:

            result = child.tick(context)

            if result == Status.SUCCESS:
                return Status.SUCCESS

            if result == Status.RUNNING:
                return Status.RUNNING

        return Status.FAILURE

class Parallel(Node):

    def __init__(self, name, children):
        super().__init__(name)
        self.children = children

    def tick(self, context):

        print(f"\n[PARALLEL] {self.name}")

        all_success = True

        for child in self.children:

            result = child.tick(context)

            if result == Status.FAILURE:
                return Status.FAILURE

            if result == Status.RUNNING:
                all_success = False

        if all_success:
            return Status.SUCCESS

        return Status.RUNNING

def is_obstacle_detected(context):
    return context["obstacle"]

def is_manual_mode(context):
    return context["manual_mode"]

def is_person_detected(context):
    return context["person_detected"]

def is_happy(context):
    return context["emotion"] == "happy"

def is_neutral(context):
    return context["emotion"] == "neutral"

def is_sad(context):
    return context["emotion"] == "sad"

def is_angry(context):
    return context["emotion"] == "angry"

def is_disgusted(context):
    return context["emotion"] == "disgusted"

def is_person_far(context):
    return context["distance"] > 2.0

def is_person_near(context):
    return context["distance"] <= 2.0

def is_person_too_close(context):
    return context["distance"] < 1.0

def is_distance_safe(context):
    return context["distance"] >= 1.0

def create_happy_behavior():

    happy_far = Sequence(
        "Happy + Person Far",
        [

            Condition(
                "Is Person Far?",
                is_person_far
            ),

            Parallel(
                "Approach Fast + Playful Wiggle",
                [

                    Action(
                        "Approach Person Quickly",
                        "APPROACH_FAST"
                    ),

                    Action(
                        "Playful Wiggle",
                        "PLAYFUL_WIGGLE"
                    )
                ]
            )
        ]
    )

    happy_near = Sequence(
        "Happy + Person Near",
        [

            Condition(
                "Is Person Near?",
                is_person_near
            ),

            Action(
                "Playful Wiggle",
                "PLAYFUL_WIGGLE"
            )
        ]
    )

    happy_distance_selector = Selector(
        "Happy Distance Selector",
        [
            happy_far,
            happy_near
        ]
    )

    return Sequence(
        "HAPPY Behavior",
        [

            Condition(
                "Is Happy?",
                is_happy
            ),

            happy_distance_selector
        ]
    )

def create_neutral_behavior():

    return Sequence(
        "NEUTRAL Behavior",
        [

            Condition(
                "Is Neutral?",
                is_neutral
            ),

            Action(
                "Observe Person",
                "OBSERVE"
            )
        ]
    )

def create_sad_behavior():

    sad_far = Sequence(
        "Sad + Person Far",
        [

            Condition(
                "Is Person Far?",
                is_person_far
            ),

            Parallel(
                "Approach Slowly + Comfort Animation",
                [

                    Action(
                        "Approach Person Slowly",
                        "APPROACH_SLOW"
                    ),

                    Action(
                        "Sad / Comfort Animation",
                        "SAD_COMFORT_ANIMATION"
                    )
                ]
            )
        ]
    )

    sad_near = Sequence(
        "Sad + Person Near",
        [

            Condition(
                "Is Person Near?",
                is_person_near
            ),

            Action(
                "Comfort and Stay",
                "COMFORT_AND_STAY"
            )
        ]
    )

    sad_distance_selector = Selector(
        "Sad Distance Selector",
        [
            sad_far,
            sad_near
        ]
    )

    return Sequence(
        "SAD Behavior",
        [

            Condition(
                "Is Sad?",
                is_sad
            ),

            sad_distance_selector
        ]
    )

def create_angry_behavior():

    angry_too_close = Sequence(
        "Angry + Person Too Close",
        [

            Condition(
                "Is Person Too Close?",
                is_person_too_close
            ),

            Action(
                "Move Away From Person",
                "MOVE_AWAY"
            )
        ]
    )

    angry_safe = Sequence(
        "Angry + Safe Distance",
        [

            Condition(
                "Is Distance Safe?",
                is_distance_safe
            ),

            Action(
                "Stay Still",
                "STAY"
            )
        ]
    )

    angry_distance_selector = Selector(
        "Angry Distance Selector",
        [
            angry_too_close,
            angry_safe
        ]
    )

    return Sequence(
        "ANGRY Behavior",
        [

            Condition(
                "Is Angry?",
                is_angry
            ),

            angry_distance_selector
        ]
    )

def create_disgusted_behavior():

    return Sequence(
        "DISGUSTED Behavior",
        [

            Condition(
                "Is Disgusted?",
                is_disgusted
            ),

            Action(
                "Pause",
                "PAUSE"
            ),

            Action(
                "Inspect Situation",
                "INSPECT"
            ),

            Action(
                "Retreat",
                "RETREAT"
            )
        ]
    )

def create_safety_behavior():

    return Sequence(
        "SAFETY",
        [

            Condition(
                "Is Obstacle Detected?",
                is_obstacle_detected
            ),

            Action(
                "Stop Robot",
                "STOP"
            )
        ]
    )

def create_manual_behavior():

    return Sequence(
        "MANUAL MODE",
        [

            Condition(
                "Is Manual Mode?",
                is_manual_mode
            ),

            Action(
                "Manual Control",
                "MANUAL_CONTROL"
            )
        ]
    )

def create_person_behavior():

    emotion_selector = Selector(
        "Emotion Selector",
        [

            create_happy_behavior(),

            create_neutral_behavior(),

            create_sad_behavior(),

            create_angry_behavior(),

            create_disgusted_behavior()
        ]
    )

    return Sequence(
        "PERSON BEHAVIOR",
        [

            Condition(
                "Is Person Detected?",
                is_person_detected
            ),

            emotion_selector
        ]
    )

def create_idle_behavior():

    return Action(
        "Idle",
        "IDLE"
    )

def create_behavior_tree():

    root = Selector(
        "ROBO PET ROOT",
        [

            create_safety_behavior(),

            create_manual_behavior(),

            create_person_behavior(),

            create_idle_behavior()
        ]
    )

    return root

def run_test(test_name, context):

    print("\n")
    print("=" * 60)
    print(f"TEST: {test_name}")
    print("=" * 60)

    print(f"Person detected : {context['person_detected']}")
    print(f"Emotion         : {context['emotion']}")
    print(f"Distance        : {context['distance']} m")
    print(f"Obstacle        : {context['obstacle']}")
    print(f"Manual mode     : {context['manual_mode']}")

    context["selected_action"] = None

    tree = create_behavior_tree()

    result = tree.tick(context)

    print("\n" + "-" * 60)
    print(f"FINAL RESULT    : {result.name}")
    print(f"SELECTED ACTION : {context['selected_action']}")
    print("=" * 60)

run_test(
    "Happy person far away",

    {
        "person_detected": True,
        "emotion": "happy",
        "distance": 3.0,
        "obstacle": False,
        "manual_mode": False
    }
)

run_test(
    "Happy person nearby",

    {
        "person_detected": True,
        "emotion": "happy",
        "distance": 0.8,
        "obstacle": False,
        "manual_mode": False
    }
)

run_test(
    "Neutral person",

    {
        "person_detected": True,
        "emotion": "neutral",
        "distance": 2.0,
        "obstacle": False,
        "manual_mode": False
    }
)

run_test(
    "Sad person far away",

    {
        "person_detected": True,
        "emotion": "sad",
        "distance": 3.5,
        "obstacle": False,
        "manual_mode": False
    }
)

run_test(
    "Sad person nearby",

    {
        "person_detected": True,
        "emotion": "sad",
        "distance": 1.2,
        "obstacle": False,
        "manual_mode": False
    }
)

run_test(
    "Angry person too close",

    {
        "person_detected": True,
        "emotion": "angry",
        "distance": 0.5,
        "obstacle": False,
        "manual_mode": False
    }
)

run_test(
    "Angry person at safe distance",

    {
        "person_detected": True,
        "emotion": "angry",
        "distance": 2.5,
        "obstacle": False,
        "manual_mode": False
    }
)

run_test(
    "Disgusted person",

    {
        "person_detected": True,
        "emotion": "disgusted",
        "distance": 2.0,
        "obstacle": False,
        "manual_mode": False
    }
)

run_test(
    "No person detected",

    {
        "person_detected": False,
        "emotion": "neutral",
        "distance": 0.0,
        "obstacle": False,
        "manual_mode": False
    }
)

run_test(
    "Obstacle detected while person is happy",

    {
        "person_detected": True,
        "emotion": "happy",
        "distance": 3.0,
        "obstacle": True,
        "manual_mode": False
    }
)

run_test(
    "Obstacle detected during manual mode",

    {
        "person_detected": True,
        "emotion": "happy",
        "distance": 2.0,
        "obstacle": True,
        "manual_mode": True
    }
)

run_test(
    "Manual mode active",

    {
        "person_detected": True,
        "emotion": "happy",
        "distance": 3.0,
        "obstacle": False,
        "manual_mode": True
    }
)

run_test(
    "Autonomous mode - happy person",

    {
        "person_detected": True,
        "emotion": "happy",
        "distance": 3.0,
        "obstacle": False,
        "manual_mode": False
    }
)

run_test(
    "Autonomous mode - sad person",

    {
        "person_detected": True,
        "emotion": "sad",
        "distance": 3.0,
        "obstacle": False,
        "manual_mode": False
    }
)
