module int_add (
    input wire clk,
    input wire rst,
    input wire add_ready,
    input wire add_accept,
    output reg add_valid,
    input wire [31:0] a,
    input wire [31:0] b,
    output reg [31:0] c
);
    localparam idle = 0;
    localparam fin = 1;
    localparam calc = 2;
    reg [31:0] d;
    reg [1:0] state;
    wire [31:0] e;

    assign e = 2 * d;

    always @(posedge clk) begin
        if (rst) begin
            d <= 0;
            state <= 0;
            add_valid <= 0;
            c <= 0;
        end else begin
            case (state)
                idle: begin
                    add_valid <= 0;
                    c <= 0;
                end
                fin: begin
                    add_valid <= 1;
                    c <= d;
                end
                calc: begin
                    d <= a + b;
                end
            endcase
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            state <= 0;
        end else begin
            case (state)
                fin: begin
                    if (add_accept) begin
                        state <= idle;
                    end
                end
                idle: begin
                    if (add_ready == 1) begin
                        state <= calc;
                    end
                end
                calc: begin
                    state <= fin;
                end
            endcase
        end
    end

endmodule
