tailwind-dev:
	npx @tailwindcss/cli -i ./src/input.css -o ./static/css/tailwind_output.css --watch

tailwind-prod:
	npx @tailwindcss/cli -i ./src/input.css -o ./static/css/tailwind.min.css --minify

docker-build:
	docker build -t pomodoro-timer .