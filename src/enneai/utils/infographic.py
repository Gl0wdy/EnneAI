from html import escape
from pathlib import Path
from types import SimpleNamespace
from typing import Sequence


def build_infographic(
	users: Sequence[object],
	messages: Sequence[object],
	snapshots: Sequence[object] = (),
) -> bytes:
	active_users = sum(not user.new for user in users)
	requests_left = sum(user.request_remain for user in users)
	bar_width = 480
	max_value = max(len(users), len(messages), active_users, 1)

	def bar(label: str, value: int, y: int, color: str) -> str:
		length = round(bar_width * value / max_value)
		return (
			f'<text x="80" y="{y}" class="label">{escape(label)}</text>'
			f'<rect x="330" y="{y - 28}" width="{bar_width}" height="34" rx="8" fill="#e5e7eb"/>'
			f'<rect x="330" y="{y - 28}" width="{length}" height="34" rx="8" fill="{color}"/>'
			f'<text x="840" y="{y}" class="value">{value}</text>'
		)

	def line(points: list[tuple[float, float]], color: str) -> str:
		if not points:
			return ''
		return f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'

	chart_snapshots = list(snapshots)
	chart_width = 900
	chart_height = 220
	chart_top = 370
	chart_bottom = chart_top + chart_height
	chart_max = max(
		(max((snapshot.users_count for snapshot in chart_snapshots), default=0)),
		(max((snapshot.messages_count for snapshot in chart_snapshots), default=0)),
		1,
	)
	user_points = []
	message_points = []
	for index, snapshot in enumerate(chart_snapshots):
		x = 150 + index * chart_width / max(len(chart_snapshots) - 1, 1)
		user_y = chart_bottom - snapshot.users_count / chart_max * chart_height
		message_y = chart_bottom - snapshot.messages_count / chart_max * chart_height
		user_points.append((x, user_y))
		message_points.append((x, message_y))
	chart = (
		f'<line x1="150" y1="{chart_top}" x2="150" y2="{chart_bottom}" stroke="#cbd5e1"/>'
		f'<line x1="150" y1="{chart_bottom}" x2="1050" y2="{chart_bottom}" stroke="#cbd5e1"/>'
		f'{line(user_points, "#0f766e")}{line(message_points, "#2563eb")}'
	)
	if not chart_snapshots:
		chart += '<text x="430" y="490" class="empty">Пока нет сохранённых снимков</text>'

	svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760">
<rect width="1200" height="760" fill="#f8fafc"/>
<rect x="40" y="40" width="1120" height="680" rx="24" fill="white" stroke="#dbe3ea"/>
<text x="80" y="115" class="title">EnneAI / отчёт администратора</text>
<text x="80" y="155" class="subtitle">Сводка по состоянию бота</text>
<text x="80" y="230" class="metric">{len(users)}</text><text x="80" y="265" class="metric-label">пользователей</text>
<text x="370" y="230" class="metric">{active_users}</text><text x="370" y="265" class="metric-label">заполнили профиль</text>
<text x="730" y="230" class="metric">{len(messages)}</text><text x="730" y="265" class="metric-label">обработано запросов</text>
<text x="80" y="345" class="section">Динамика статистики</text>
{chart}
<text x="180" y="650" class="legend users">Пользователи</text><text x="390" y="650" class="legend messages">Запросы</text>
<text x="700" y="650" class="footer">Осталось запросов: {requests_left}</text>
<style>.title{{font:700 34px sans-serif;fill:#172033}}.subtitle{{font:20px sans-serif;fill:#64748b}}.metric{{font:700 44px sans-serif;fill:#172033}}.metric-label,.footer{{font:18px sans-serif;fill:#64748b}}.section{{font:700 22px sans-serif;fill:#172033}}.legend,.empty{{font:18px sans-serif;fill:#64748b}}.users{{fill:#0f766e}}.messages{{fill:#2563eb}}</style>
</svg>'''
	return svg.encode('utf-8')


def main() -> None:
	test_users = [
		SimpleNamespace(new=False, request_remain=11),
		SimpleNamespace(new=False, request_remain=4),
		SimpleNamespace(new=True, request_remain=15),
		SimpleNamespace(new=False, request_remain=0),
	]
	test_messages = [SimpleNamespace() for _ in range(9)]
	test_snapshots = [
		SimpleNamespace(users_count=2, messages_count=1),
		SimpleNamespace(users_count=3, messages_count=5),
		SimpleNamespace(users_count=4, messages_count=9),
	]
	output_path = Path(__file__).resolve().parents[3] / 'enneai-infographic-test.svg'
	output_path.write_bytes(build_infographic(test_users, test_messages, test_snapshots))
	print(f'Инфографика создана: {output_path}')


if __name__ == '__main__':
	main()