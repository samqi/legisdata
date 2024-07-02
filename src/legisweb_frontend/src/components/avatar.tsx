import { Col, Image } from "react-bootstrap";
import * as Icon from "react-bootstrap-icons";
import * as Schema from "../schema";

export default function Avatar({
  idx,
  person,
}: {
  idx: number;
  person: Schema.Person;
}) {
  return idx == 0 ? (
    <Col className="clearfix d-none d-sm-block" md={2}>
      {person == null || person.image_url == null ? (
        <span
          style={{
            width: "3em",
            height: "3em",
            padding: "0.5em",
            textAlign: "center",
            backgroundColor: "#DDD",
          }}
          className="rounded-circle float-end"
        >
          <Icon.Person />
        </span>
      ) : (
        <Image
          src=""
          roundedCircle
          className="float-end"
          style={{
            width: "3em",
            height: "3em",
            backgroundColor: "#DDD",
          }}
        />
      )}
    </Col>
  ) : (
    <></>
  );
}
