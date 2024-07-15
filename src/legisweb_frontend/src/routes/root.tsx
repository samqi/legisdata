import "bootstrap/dist/css/bootstrap.min.css";
import { type ReactNode, useEffect, useRef } from "react";
import * as Icon from "react-bootstrap-icons";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import InputGroup from "react-bootstrap/InputGroup";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import Row from "react-bootstrap/Row";
import Stack from "react-bootstrap/Stack";
import Toast from "react-bootstrap/Toast";
import ToastContainer from "react-bootstrap/ToastContainer";
import { useDispatch, useSelector } from "react-redux";
import {
	Link,
	Outlet,
	useLocation,
	useOutlet,
	useSubmit,
} from "react-router-dom";
import type { RootState } from "../app/store";
import { submit } from "../features/search/query-slice";
import { hide as toastHide } from "../features/toast/toast-slice";
import "./Root.css";

function Home() {
	return (
		<>
			<h1>Welcome to Legislative Data Web Viewer</h1>
			<div>
				This is a web viewer for legislative data archive for Selangor state
				Assembly. Try having a look to the list of{" "}
				<Link to="/hansard">hansards</Link> or{" "}
				<Link to="/inquiry">inquiries</Link> to begin.
			</div>
		</>
	);
}

function Navigation() {
  const dispatch = useDispatch();
		const submitForm = useSubmit();
		const location = useLocation();

		return (
			<Navbar bg="primary" expand="lg">
				<Container>
					<Navbar.Brand as={Link} className="text-bg-primary" to="/">
						Legisdata Web Viewer
					</Navbar.Brand>
					<Navbar.Toggle aria-controls="navbarScroll" />
					<Navbar.Collapse id="navbarScroll">
						<Nav className="me-auto" navbarScroll>
							<Nav.Link className="text-bg-primary" to="/" as={Link}>
								Home
							</Nav.Link>
							<Nav.Link className="text-bg-primary" to="/hansard" as={Link}>
								Hansards
							</Nav.Link>
							<Nav.Link className="text-bg-primary" to="/inquiry" as={Link}>
								Inquiries
							</Nav.Link>
						</Nav>
						{location.pathname.replace(/^\/*|\/*$/g, "") !== "search" && (
							<Form
								className="d-flex"
								onSubmit={(e) => {
									e.preventDefault();
									const data = {
										// @ts-expect-error DOM
										queryText: e.target.querySelector("#quick-search-query")
											.value,
										documentType:
											// @ts-expect-error DOM
											e.target.querySelector("#quick-search-type").value,
									};
									dispatch(submit(data));

									submitForm(data, {
										method: "get",
										action: "/search",
									});

									// @ts-expect-error DOM
									e.target?.reset();
								}}
							>
								<InputGroup>
									<Form.Control name="query" id="quick-search-query" />
									<input
										type="hidden"
										name="type"
										id="quick-search-type"
										value="inquiry-title"
									/>
									<Button variant="light" type="submit">
										Search
									</Button>
								</InputGroup>
							</Form>
						)}
					</Navbar.Collapse>
				</Container>
			</Navbar>
		);
}

function Footer() {
	return (
		<footer className="text-bg-light">
			<Container className="pt-5 pb-5">
				<Row>
					<Col lg="6">
						<h4>Legisdata Web Viewer</h4>
						<p>Legislative Data project repo (parsers & sayit frontend)</p>
						<p>
							<small>
								<Link
									to="https://choosealicense.com/licenses/cc-by-4.0/"
									className="link-secondary link-underline-opacity-0"
								>
									Creative Commons Attribution 4.0 International
								</Link>
							</small>
						</p>
					</Col>
					<Col>
						<FooterLinks
							header="Links"
							linkList={[
								{
									link: "/",
									content: "Home",
								},
								{
									link: "/hansard",
									content: "Hansards",
								},
								{
									link: "/inquiry",
									content: "Inquiries",
								},
								//{
								//  link: "#people",
								//  content: "People",
								//},
								{
									link: "/search",
									content: "Search",
								},
							]}
						/>
					</Col>
					<Col>
						<FooterLinks
							header="Meta"
							linkList={[
								{
									link: "https://github.com/Sinar/legisdata/",
									content: "Project Repository",
								},
								{
									link: "https://huggingface.co/datasets/sinarproject/legisdata/",
									content: "Data Repository",
								},
								{
									link: "https://unsceb-hlcm.github.io/",
									content: "AkomaNtoso",
								},
							]}
						/>
					</Col>
					<Col>
						<FooterLinks
							header="Community"
							linkList={[
								{
									link: "https://sinarproject.org/",
									content: (
										<>
											<Icon.Globe /> Sinar Project
										</>
									),
								},
								{
									link: "https://x.com/sinarproject/",
									content: (
										<>
											<Icon.TwitterX /> X / Twitter
										</>
									),
								},
								{
									link: "https://facebook.com/sinarproject/",
									content: (
										<>
											<Icon.Facebook /> Facebook
										</>
									),
								},
								{
									link: "https://instagram.com/sinarproject/",
									content: (
										<>
											<Icon.Instagram /> Instagram
										</>
									),
								},
								{
									link: "https://github.com/Sinar/",
									content: (
										<>
											<Icon.Github /> Github
										</>
									),
								},
							]}
						/>
					</Col>
				</Row>
			</Container>
		</footer>
	);
}

function FooterLinks({
	header,
	linkList,
}: {
	header: string;
	linkList: Array<{ content: ReactNode; link: string }>;
}) {
	return (
		<>
			<h5>{header}</h5>
			<ul>
				{linkList.map((item, idx) => (
					<li key={"li-".concat(idx.toString())}>
						<Link
							className="link-secondary link-underline-opacity-0"
							to={item.link}
						>
							{item.content}
						</Link>
					</li>
				))}
			</ul>
		</>
	);
}

export default function Root() {
	const toast = useSelector((state: RootState) => state.toast);
	const dispatch = useDispatch();
	const location = useLocation();

	// https://stackoverflow.com/a/78396559/5742
	const mostRecentScrollToHash = useRef<string>("");
	const scrollToHash = (): void => {
		if (location.hash) {
			const hash = location.hash.replace("#", "");
			const element = document.getElementById(hash);
			if (element && hash !== mostRecentScrollToHash.current) {
				element.scrollIntoView({
					behavior: "smooth",
				});
				mostRecentScrollToHash.current = hash;
			}
		}
	};

	useEffect(scrollToHash);

	return (
		<>
			<Navigation />

			<ToastContainer className="fixed-top" position="top-center">
				<Toast
					show={toast.show}
					bg={toast.variant}
					onClose={() => dispatch(toastHide())}
					autohide={true}
				>
					<Toast.Body>{toast.message}</Toast.Body>
				</Toast>
			</ToastContainer>

			<Container id="detail" className="pt-5 pb-5">
				<Stack gap={3}>{useOutlet() === null ? <Home /> : <Outlet />}</Stack>
			</Container>

			<Footer />
		</>
	);
}
