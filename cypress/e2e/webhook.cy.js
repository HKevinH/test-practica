describe("Chat alert API", () => {
  it("returns alert true when the message contains a keyword", () => {
    cy.request("POST", "/webhook", {
      user: "Ana",
      message: "Necesito ayuda urgente con un error en producción",
    }).then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.deep.eq({ alert: true });
    });
  });

  it("returns alert false when the message does not contain a keyword", () => {
    cy.request("POST", "/webhook", {
      user: "Luis",
      message: "Hola, dejo una actualización del proyecto",
    }).then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.deep.eq({ alert: false });
    });
  });
});
