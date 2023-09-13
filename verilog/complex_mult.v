module complex_mult (
    input wire clk,
    input wire rst,
    input wire mult_ready,
    input wire mult_accept,
    output reg mult_valid,
    input wire signed [BIT*2-1:0] mult_in_a,
    input wire signed [BIT*2-1:0] mult_in_b,
    output reg signed [BIT*2-1:0] mult_out_0
);
  //localparams
  localparam mult_b1_INIT = 0;
  localparam mult_b1_S0 = 1;
  localparam mult_b1_FINISH = 2;
  localparam PRECISION = 16;
  localparam BIT = 32;

  //signals: 
  reg         [      1:0] mult_state;
  wire signed [  BIT-1:0] a_imag;
  wire signed [  BIT-1:0] a_real;
  wire signed [  BIT-1:0] b_imag;
  wire signed [  BIT-1:0] b_real;
  wire signed [BIT*2-1:0] c_imag;
  wire signed [BIT*2-1:0] c_real;
  reg signed  [BIT*2-1:0] a;
  reg signed  [BIT*2-1:0] b;
  //combinations: 
  assign a_imag = a[BIT-1:0];
  assign a_real = a[BIT*2-1:BIT];
  assign b_imag = b[BIT-1:0];
  assign b_real = b[BIT*2-1:BIT];
  assign c_imag = (a_real * b_imag + a_imag * b_real) >> PRECISION;
  assign c_real = (a_real * b_real - a_imag * b_imag) >> PRECISION;
  always @(posedge clk) begin
    if (rst) begin
      a <= 0;
      b <= 0;
      mult_out_0 <= 0;
      mult_state <= mult_b1_INIT;
    end else begin
      case (mult_state)
        mult_b1_INIT: begin
          mult_valid <= 0;
          if (mult_ready == 1) begin
            a          <= mult_in_a;
            b          <= mult_in_b;
            mult_state <= mult_b1_FINISH;
          end
        end
        mult_b1_FINISH: begin
          mult_valid <= 1;
          if (mult_accept == 1) begin
            mult_state <= mult_b1_INIT;
          end
          mult_out_0 <= {c_real[BIT-1:0], c_imag[BIT-1:0]};
        end
      endcase
    end
  end
endmodule
