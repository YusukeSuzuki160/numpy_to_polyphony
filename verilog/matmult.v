module matmult(
  input wire clk, rst,
  input wire [31:0] a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8,
  input wire [31:0] b_0, b_1, b_2, b_3, b_4, b_5, b_6, b_7, b_8,
  output reg [31:0] c_0, c_1, c_2, c_3, c_4, c_5, c_6, c_7, c_8
);
  always @(posedge clk) begin
    if (rst) begin
      c_0 <= 0;
      c_1 <= 0;
      c_2 <= 0;
      c_3 <= 0;
      c_4 <= 0;
      c_5 <= 0;
      c_6 <= 0;
      c_7 <= 0;
      c_8 <= 0;
    end else begin
      c_0 <= a_0 * b_0 + a_1 * b_3 + a_2 * b_6;
      c_1 <= a_0 * b_1 + a_1 * b_4 + a_2 * b_7;
      c_2 <= a_0 * b_2 + a_1 * b_5 + a_2 * b_8;
      c_3 <= a_3 * b_0 + a_4 * b_3 + a_5 * b_6;
      c_4 <= a_3 * b_1 + a_4 * b_4 + a_5 * b_7;
      c_5 <= a_3 * b_2 + a_4 * b_5 + a_5 * b_8;
      c_6 <= a_6 * b_0 + a_7 * b_3 + a_8 * b_6;
      c_7 <= a_6 * b_1 + a_7 * b_4 + a_8 * b_7;
      c_8 <= a_6 * b_2 + a_7 * b_5 + a_8 * b_8;
    end
  end
endmodule