from flask import render_template, redirect, Blueprint, abort, request
from app import Tournament, User, Team, session
from app.forms import LoginForm, RegisterForm, TournamentInfoForm, TeamForm
from flask_login import login_user, logout_user, login_required, current_user

from pprint import pprint


blueprint = Blueprint("matboy_pages", __name__, template_folder='templates')


@blueprint.route("/")
@blueprint.route("/index")
def index_page():
    tournaments = Tournament.query.all()
    return render_template("index.html", tournaments=tournaments)


@blueprint.route("/login", methods=["POST", "GET"])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email == form.email.data).first()
        if not user:
            form.email.errors.append(
                "Пользователь с таким e-mail не зарегестрирован")
        elif not user.check_password(form.password.data):
            form.password.errors.append("Неправильный пароль")
        else:
            login_user(user, remember=True)
            return redirect("/")
    return render_template("login.html", form=form)


@blueprint.route("/register", methods=["POST", "GET"])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User().fill(email=form.email.data,
                           name=form.name.data,
                           surname=form.surname.data,
                           patronymic=form.patronymic.data,
                           city=form.city.data,
                           birthday=form.birthday.data,)
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect("/login")
    return render_template("register.html", form=form)


@blueprint.route("/logout")
@login_required
def logout_page():
    logout_user()
    print(request.environ)
    return redirect(request.environ)


@blueprint.route("/new_tournament", methods=["POST", "GET"])
@login_required
def tournament_creator_page():
    if not current_user.is_creator:
        abort(403)
    form = TournamentInfoForm()
    if form.validate_on_submit():
        if Tournament.query.filter(Tournament.title == form.title.data).first():
            form.title.errors.append("Турнир с таким названием уже существует")
        tournament = Tournament().fill(title=form.title.data,
                                       description=form.description.data,
                                       place=form.place.data,
                                       start=form.start.data,
                                       end=form.end.data,)
        current_user.tournaments.append(tournament)
        session.merge(current_user)
        session.commit()

        return redirect("/")
    return render_template("tournament_editor.html", form=form)


@blueprint.route("/edit_tournament/<int:tour_id>", methods=["POST", "GET"])
@login_required
def tournament_edit_page(tour_id: int):
    tour = Tournament.query.get(tour_id)
    if not (current_user.id == 1 or tour.chief_id == current_user.id):
        abort(403)
    form = TournamentInfoForm()
    if form.validate_on_submit():
        new_title = form.title.data
        # if title changed and new_title exist
        if (new_title != tour.title and (
                Tournament.query.filter(Tournament.title == new_title).first()
        )):
            form.title.errors.append("Турнир с таким названием уже существует")
            return render_template("tournament_editor.html", form=form)

        # Change tour values
        tour.title = new_title
        tour.description = form.description.data
        tour.place = form.place.data
        tour.start = form.start.data
        tour.end = form.end.data
        session.merge(tour)
        session.commit()

        return redirect("/")

    elif not form.is_submitted():
        form.title.data = tour.title
        form.description.data = tour.description
        form.place.data = tour.place
        form.start.data = tour.start
        form.end.data = tour.end

    return render_template("tournament_editor.html", form=form)


@blueprint.route("/team_request/<int:tour_id>", methods=["GET", "POST"])
@login_required
def team_request(tour_id: int):
    form = TeamForm()
    tour = Tournament.query.get(tour_id)
    if not tour:
        abort(404)
    if form.validate_on_submit():
        team = Team().fill(
            name=form.name.data,
            motto=form.motto.data,
            trainer_id=current_user.id,
            tournament_id=tour.id,
        )

        # for email in form.players.data:
        #     user = session.query(User).filter(User.email==email)
        #     if not user:
        #         return render_template("team_request.html", tour=tour, form=form, message=message)
        #     team.players.append(user)
        session.add(team)
        session.commit()
        return redirect(f"/tournament/{tour_id}")

    return render_template("team_request.html", tour=tour, form=form)
