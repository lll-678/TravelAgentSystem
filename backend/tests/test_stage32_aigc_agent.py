from app.api.v1.aigc import AigcAgentRequest, StoryboardRequest, aigc_agent, storyboard
from app.services.aigc_agent_service import run_aigc_agent


def test_aigc_agent_returns_result_and_trace() -> None:
    payload = AigcAgentRequest(
        task="diary_animation",
        text="从校门出发，经过食堂和图书馆，记录一次沙河校区游览。",
        destination_name="北京邮电大学沙河校区",
        style="cinematic",
        media_urls=["/media/demo/library.jpg", "/media/demo/route.mp4"],
        scene_count=5,
        user_id=1,
    )

    result = aigc_agent(payload)

    assert result["result"]["title"].startswith("北京邮电大学沙河校区")
    assert len(result["result"]["storyboard"]) == 5
    assert result["result"]["media_analysis"]["image_count"] == 1
    assert result["result"]["media_analysis"]["video_count"] == 1
    assert result["result"]["simulated_video_url"].startswith("https://example.local/aigc/agent/")
    assert result["result"]["compression"]["original_size"] > 0
    assert len(result["agent_trace"]["steps"]) >= 4
    assert result["agent_trace"]["steps"][0]["tool"] == "media_analyzer"
    assert all(step["status"] == "success" for step in result["agent_trace"]["steps"])
    assert result["agent_trace"]["total_duration_ms"] == sum(
        step["duration_ms"] for step in result["agent_trace"]["steps"]
    )
    assert result["algorithm_trace"]["tool_count"] == str(len(result["agent_trace"]["steps"]))
    assert result["algorithm_trace"]["media_inputs"] == "2"
    assert result["algorithm_trace"]["network"] == "disabled"


def test_aigc_agent_media_inputs_change_storyboard_keywords() -> None:
    without_media = run_aigc_agent(
        {
            "task": "storyboard",
            "text": "完成一次校园路线记录。",
            "destination_name": "北京邮电大学沙河校区",
            "media_urls": [],
            "scene_count": 2,
        }
    )
    with_media = run_aigc_agent(
        {
            "task": "storyboard",
            "text": "完成一次校园路线记录。",
            "destination_name": "北京邮电大学沙河校区",
            "media_urls": ["/media/demo/food-photo.png"],
            "scene_count": 2,
        }
    )

    assert without_media["result"]["media_analysis"]["media_count"] == 0
    assert with_media["result"]["media_analysis"]["media_count"] == 1
    assert "照片素材" in with_media["result"]["media_analysis"]["keywords"]
    assert without_media["result"]["storyboard"][0]["description"] != with_media["result"]["storyboard"][0][
        "description"
    ]


def test_aigc_legacy_storyboard_remains_compatible() -> None:
    board = storyboard(
        StoryboardRequest(
            text="从校门走到食堂，再去图书馆。",
            scene_count=3,
            media_urls=["/media/demo/campus-photo.jpg"],
        )
    )

    assert len(board["scenes"]) == 3
    assert board["algorithm_trace"]["mode"] == "mock AIGC storyboard generator"
